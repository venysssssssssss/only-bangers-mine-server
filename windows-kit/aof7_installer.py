"""AOF7 Windows installer entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import hashlib
import logging
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote, unquote, urlparse, urlsplit, urlunsplit


@dataclass(frozen=True)
class ManifestEntry:
    url: str
    filename: str
    project_id: int | None
    file_id: int | None


@dataclass(frozen=True)
class PackManifest:
    minecraft_version: str
    loader_version: str
    entries: tuple[ManifestEntry, ...]


@dataclass(frozen=True)
class DownloadRecord:
    url: str
    path: str
    size: int
    sha256: str


class DownloadFailure(RuntimeError):
    pass


def _request_url(url: str) -> str:
    parts = urlsplit(url)
    path = quote(parts.path, safe="/%:@!$&'()*+,;=-._~")
    query = quote(parts.query, safe="=&/?@:+,;$-_.!~*'()/%")
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def _relative_mod_path(filename: object) -> str:
    if not isinstance(filename, str) or not filename or "\x00" in filename:
        raise ValueError("manifest filename must be a non-empty string")
    normalized = filename.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"absolute manifest path is not allowed: {filename!r}")
    parts = normalized.split("/")
    if any(part in ("", "..") for part in parts):
        raise ValueError(f"invalid manifest path: {filename!r}")
    clean = str(PurePosixPath(*parts))
    if not clean.startswith("mods/") or clean == "mods":
        raise ValueError(f"manifest path must be under mods/: {filename!r}")
    return clean


def load_manifest(
    path: Path,
    expected_minecraft: str = "1.20.1",
    expected_loader: str = "0.16.0",
) -> PackManifest:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")

    minecraft = data.get("minecraft")
    if not isinstance(minecraft, dict) or minecraft.get("version") != expected_minecraft:
        raise ValueError(f"manifest must target Minecraft {expected_minecraft}")
    loaders = minecraft.get("modLoaders")
    expected_loader_id = f"fabric-{expected_loader}"
    if not isinstance(loaders, list) or len(loaders) != 1:
        raise ValueError("manifest must contain exactly one mod loader")
    if not isinstance(loaders[0], dict) or loaders[0].get("id") != expected_loader_id:
        raise ValueError(f"manifest must use Fabric Loader {expected_loader}")

    raw_files = data.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise ValueError("manifest must contain a non-empty files list")
    entries: list[ManifestEntry] = []
    seen_urls: set[str] = set()
    for raw in raw_files:
        if not isinstance(raw, dict):
            raise ValueError("manifest file entries must be objects")
        url = raw.get("downloadUrl")
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed is None or parsed.scheme.lower() != "https" or not parsed.netloc:
            raise ValueError(f"manifest downloadUrl must be HTTPS: {url!r}")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("manifest URLs must not contain credentials")
        raw_filename = raw.get("filename")
        if not raw_filename:
            raw_filename = f"mods/{unquote(Path(parsed.path).name)}"
        filename = _relative_mod_path(raw_filename)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        entries.append(
            ManifestEntry(
                url=url,
                filename=filename,
                project_id=raw.get("projectID") if isinstance(raw.get("projectID"), int) else None,
                file_id=raw.get("fileID") if isinstance(raw.get("fileID"), int) else None,
            )
        )
    return PackManifest(expected_minecraft, expected_loader, tuple(entries))


def safe_join(root: Path, relative: str) -> Path:
    base = root.resolve()
    target = (base / relative.replace("\\", "/")).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"path escapes output root: {relative!r}") from exc
    return target


def copy_overrides(source: Path, destination: Path) -> int:
    if not source.exists():
        return 0
    copied = 0
    destination.mkdir(parents=True, exist_ok=True)
    for current, dirs, files in os.walk(source, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if not (current_path / name).is_symlink()]
        for name in files:
            source_path = current_path / name
            if source_path.is_symlink():
                continue
            relative = source_path.relative_to(source)
            target = safe_join(destination, str(relative))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
            copied += 1
    return copied


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_state(path: Path) -> dict[str, DownloadRecord]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    raw_records = data.get("files", []) if isinstance(data, dict) else []
    records: dict[str, DownloadRecord] = {}
    for raw in raw_records:
        if not isinstance(raw, dict):
            continue
        try:
            record = DownloadRecord(
                url=str(raw["url"]),
                path=str(raw["path"]),
                size=int(raw["size"]),
                sha256=str(raw["sha256"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        records[record.path] = record
    return records


def _write_state(path: Path, records: dict[str, DownloadRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": [record.__dict__ for record in sorted(records.values(), key=lambda item: item.path)]
    }
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _mod_target(mods_root: Path, filename: str) -> Path:
    relative = filename.removeprefix("mods/")
    return safe_join(mods_root, relative)


def _verified_record(entry: ManifestEntry, target: Path, record: DownloadRecord | None) -> DownloadRecord | None:
    if record is None or record.url != entry.url or record.path != entry.filename or not target.is_file():
        return None
    if record.size != target.stat().st_size:
        return None
    try:
        if sha256_file(target) != record.sha256:
            return None
    except OSError:
        return None
    return record


def _download_one(entry: ManifestEntry, mods_root: Path, attempts: int) -> DownloadRecord:
    target = _mod_target(mods_root, entry.filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            offset = part.stat().st_size if part.is_file() else 0
            headers = {"User-Agent": "OnlyBangers-AOF7-Installer/2.5.3"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
            response = urlopen(Request(_request_url(entry.url), headers=headers), timeout=20)
            status = getattr(response, "status", None) or response.getcode()
            append = bool(offset and status == 206)
            if offset and status != 206:
                append = False
                offset = 0
            mode = "ab" if append else "wb"
            with response, part.open(mode) as stream:
                expected_length = response.headers.get("Content-Length")
                expected_length = int(expected_length) if expected_length else None
                written = 0
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    stream.write(block)
                    written += len(block)
                stream.flush()
                os.fsync(stream.fileno())
            if expected_length is not None and written != expected_length:
                raise IOError(f"short download for {entry.url}: {written}/{expected_length} bytes")
            size = part.stat().st_size
            digest = sha256_file(part)
            os.replace(part, target)
            return DownloadRecord(entry.url, entry.filename, size, digest)
        except HTTPError as exc:
            last_error = exc
            retryable = exc.code in {429, 500, 502, 503, 504}
            exc.close()
        except (ConnectionResetError, TimeoutError, URLError, OSError) as exc:
            last_error = exc
            retryable = True
        if not retryable or attempt + 1 >= attempts:
            break
        time.sleep(min(2.0, 0.25 * (2**attempt) + random.uniform(0, 0.1)))
    try:
        part.unlink(missing_ok=True)
    except OSError:
        pass
    raise RuntimeError(f"download failed for {entry.filename} ({entry.url}): {last_error}") from last_error


def download_entries(
    entries: tuple[ManifestEntry, ...],
    mods_root: Path,
    state_path: Path,
    workers: int = 8,
    attempts: int = 5,
) -> tuple[DownloadRecord, ...]:
    if workers < 1 or attempts < 1:
        raise ValueError("workers and attempts must be positive")
    mods_root.mkdir(parents=True, exist_ok=True)
    old_records = _load_state(state_path)
    results: list[DownloadRecord | None] = [None] * len(entries)
    pending: list[tuple[int, ManifestEntry]] = []
    for index, entry in enumerate(entries):
        target = _mod_target(mods_root, entry.filename)
        verified = _verified_record(entry, target, old_records.get(entry.filename))
        if verified is not None:
            results[index] = verified
        else:
            pending.append((index, entry))

    failures: list[str] = []
    completed: dict[str, DownloadRecord] = dict(old_records)
    with ThreadPoolExecutor(max_workers=min(workers, 8)) as executor:
        futures = {
            executor.submit(_download_one, entry, mods_root, attempts): (index, entry)
            for index, entry in pending
        }
        for future in as_completed(futures):
            index, entry = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # aggregate all independent download errors
                failures.append(f"{entry.filename} ({entry.url}): {exc}")
            else:
                results[index] = record
                completed[record.path] = record
    if completed != old_records:
        _write_state(state_path, completed)
    if failures:
        raise DownloadFailure("; ".join(sorted(failures)))
    return tuple(record for record in results if record is not None)


def _write_install_state(path: Path, pack: PackManifest, overrides: int) -> None:
    records = _load_state(path)
    payload = {
        "minecraft": pack.minecraft_version,
        "fabric_loader": pack.loader_version,
        "overrides": overrides,
        "files": [record.__dict__ for record in sorted(records.values(), key=lambda item: item.path)],
    }
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def merge_launcher_profile(
    profile_path: Path,
    output_root: Path,
    profile_name: str = "AOF7 2.5.3",
) -> None:
    if profile_path.is_file():
        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read launcher profile: {exc}") from exc
        backup = profile_path.with_suffix(".json.aof7-backup")
        shutil.copy2(profile_path, backup)
    else:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("launcher profile root must be an object")
    profiles = data.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("launcher profiles must be an object")
    profiles["aof7-2.5.3"] = {
        "name": profile_name,
        "type": "custom",
        "lastVersionId": "fabric-loader-0.16.0-1.20.1",
        "gameDir": str(output_root.resolve()),
    }
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = profile_path.with_name(profile_path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, profile_path)


def install_pack(
    manifest_path: Path,
    kit_root: Path,
    output_root: Path,
    workers: int = 8,
) -> dict:
    pack = load_manifest(manifest_path)
    mods_root = output_root / "mods"
    logs_root = output_root / "logs"
    output_root.mkdir(parents=True, exist_ok=True)
    mods_root.mkdir(parents=True, exist_ok=True)
    logs_root.mkdir(parents=True, exist_ok=True)
    (output_root / "tools" / "python").mkdir(parents=True, exist_ok=True)
    log_path = logs_root / f"install-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.log"
    logger = logging.getLogger("aof7_installer")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler(log_path, encoding="utf-8"))
    state_path = output_root / ".aof7-install-state.json"
    old_records = _load_state(state_path)
    skipped = sum(
        _verified_record(entry, _mod_target(mods_root, entry.filename), old_records.get(entry.filename)) is not None
        for entry in pack.entries
    )
    logger.info("validating %d manifest entries", len(pack.entries))
    download_entries(pack.entries, mods_root, state_path, workers=workers)
    copied_overrides = copy_overrides(kit_root / "overrides", output_root)
    _write_install_state(state_path, pack, copied_overrides)
    logger.info("installed %d files and copied %d overrides", len(pack.entries), copied_overrides)
    return {
        "entries": len(pack.entries),
        "downloaded": len(pack.entries) - skipped,
        "skipped": skipped,
        "overrides": copied_overrides,
        "state_path": str(state_path),
    }


def _default_documents() -> Path:
    documents = os.environ.get("USERPROFILE")
    if documents:
        return Path(documents) / "Documents"
    return Path.home() / "Documents"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install All of Fabric 7 2.5.3")
    parser.add_argument("--manifest")
    parser.add_argument("--kit-root")
    parser.add_argument("--output-root")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--merge-profile", action="store_true")
    parser.add_argument("--profile-path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.self_test:
        print("aof7-installer self-test: ok")
        return 0
    if args.merge_profile:
        if not args.profile_path or not args.output_root:
            parser.error("--merge-profile requires --profile-path and --output-root")
        try:
            merge_launcher_profile(Path(args.profile_path).resolve(), Path(args.output_root).resolve())
            return 0
        except (OSError, ValueError) as exc:
            print(f"aof7-installer error: {exc}", file=sys.stderr)
            return 1
    kit_root = Path(args.kit_root).resolve() if args.kit_root else Path(__file__).resolve().parent
    manifest_path = Path(args.manifest).resolve() if args.manifest else kit_root / "manifest.json"
    output_root = Path(args.output_root).resolve() if args.output_root else _default_documents() / "AOF7-2.5.3"
    try:
        pack = load_manifest(manifest_path)
        if args.check_only:
            print(json.dumps({
                "minecraft": pack.minecraft_version,
                "loader": pack.loader_version,
                "entries": len(pack.entries),
            }, sort_keys=True))
            return 0
        print(json.dumps(install_pack(manifest_path, kit_root, output_root, workers=args.workers), sort_keys=True))
        return 0
    except (DownloadFailure, OSError, ValueError) as exc:
        print(f"aof7-installer error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
