# AOF7 Windows Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a double-click Windows kit that installs the AOF7 2.5.3 client from a local CurseForge manifest into `Documents\AOF7-2.5.3` and prepares the official Minecraft Launcher profile.

**Architecture:** A CMD entrypoint invokes a process-local PowerShell bootstrap. PowerShell downloads and verifies a pinned embeddable Python runtime, then Python validates the manifest, downloads the mod files concurrently with resumable atomic writes, copies overrides, and records state. PowerShell uses the official Fabric installer and a backed-up launcher profile to point the official launcher at the isolated output directory.

**Tech Stack:** Windows CMD, Windows PowerShell 5.1+, Python 3.12.10 embeddable runtime, Python standard library only, official Fabric Installer 1.0.0, `unittest`, `http.server`, and `zipfile`.

**Spec:** `docs/superpowers/specs/2026-09-11-aof7-windows-kit-design.md`

## Global Constraints

- Modpack: All of Fabric 7 `2.5.3`.
- Minecraft: `1.20.1`.
- Fabric Loader: `0.16.0`.
- Python bootstrap: official Python `3.12.10` embeddable archive, architecture-matched.
- Output: `C:\Users\<current-user>\Documents\AOF7-2.5.3`.
- No administrator elevation, system Python changes, `pip`, or third-party Python packages.
- Input manifest is adjacent to `Install-AOF7.cmd` and must be consumed rather than replaced by a hard-coded mod list.
- Only HTTPS manifest URLs are accepted in normal mode.
- Existing valid files remain in place if a replacement download fails.
- No Microsoft credentials or launcher tokens are read or logged.
- Do not bundle third-party mod binaries in the distributable kit.
- No Git repository is available in this workspace; use `git diff --check` only when Git metadata exists.

---

### Task 1: Create the kit shell and test harness

**Files:**
- Create: `windows-kit/Install-AOF7.cmd`
- Create: `windows-kit/Install-AOF7.ps1`
- Create: `windows-kit/aof7_installer.py`
- Create: `windows-kit/README.md`
- Create: `tests/test_aof7_installer.py`
- Create: `tests/fixtures/manifest-minimal.json`

**Interfaces:**
- `Install-AOF7.cmd` forwards all arguments to `Install-AOF7.ps1` using a process-local execution-policy bypass.
- `Install-AOF7.ps1` accepts `-KitRoot`, `-OutputRoot`, `-ManifestPath`, and `-CheckOnly`.
- `aof7_installer.py` exposes `main(argv: list[str] | None) -> int` and `--self-test`.

- [ ] **Step 1: Write the failing entrypoint tests**

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
KIT = ROOT / "windows-kit"


class EntrypointTests(unittest.TestCase):
    def test_cmd_forwards_to_powershell(self):
        text = (KIT / "Install-AOF7.cmd").read_text(encoding="utf-8")
        self.assertIn("Install-AOF7.ps1", text)
        self.assertIn("%*", text)

    def test_python_entrypoint_exposes_self_test(self):
        text = (KIT / "aof7_installer.py").read_text(encoding="utf-8")
        self.assertIn("--self-test", text)

    def test_fixture_manifest_is_present(self):
        self.assertTrue((ROOT / "tests/fixtures/manifest-minimal.json").is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test and verify it fails for missing kit files**

Run: `python3 -m unittest tests.test_aof7_installer.EntrypointTests -v`  
Expected: FAIL because the kit files do not exist yet.

- [ ] **Step 3: Add the minimal wrappers and fixture**

Create `windows-kit/Install-AOF7.cmd` with:

```bat
@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AOF7.ps1" %*
exit /b %ERRORLEVEL%
```

Create `windows-kit/aof7_installer.py` with a `main` parser that accepts `--self-test`, prints `aof7-installer self-test: ok`, and returns `0`. Create `Install-AOF7.ps1` with parameter declarations and a `--self-test` invocation of the Python entrypoint. Create `manifest-minimal.json` containing Minecraft `1.20.1`, loader `fabric-0.16.0`, and one HTTPS file entry. Add README usage and the output path.

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `python3 -m unittest tests.test_aof7_installer.EntrypointTests -v`  
Expected: PASS with three tests.

---

### Task 2: Implement manifest validation and safe filesystem paths

**Files:**
- Modify: `windows-kit/aof7_installer.py`
- Modify: `tests/test_aof7_installer.py`

**Interfaces:**
- `ManifestEntry(url: str, filename: str, project_id: int | None, file_id: int | None)`.
- `PackManifest(minecraft_version: str, loader_version: str, entries: tuple[ManifestEntry, ...])`.
- `load_manifest(path: Path, expected_minecraft: str = "1.20.1", expected_loader: str = "0.16.0") -> PackManifest`.
- `safe_join(root: Path, relative: str) -> Path`.
- `copy_overrides(source: Path, destination: Path) -> int`.

- [ ] **Step 1: Write failing validation tests**

```python
class ManifestTests(unittest.TestCase):
    def test_loads_expected_versions_and_entries(self):
        pack = load_manifest(ROOT / "tests/fixtures/manifest-minimal.json")
        self.assertEqual(pack.minecraft_version, "1.20.1")
        self.assertEqual(pack.loader_version, "0.16.0")
        self.assertEqual(pack.entries[0].filename, "mods/example.jar")

    def test_rejects_wrong_loader(self):
        path = ROOT / "tests/fixtures/manifest-minimal.json"
        with self.assertRaises(ValueError):
            load_manifest(path, expected_loader="0.17.0")

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            safe_join(Path("/tmp/output"), "mods/../../outside.jar")

    def test_rejects_non_https_url(self):
        path = ROOT / "tests/fixtures/manifest-http.json"
        with self.assertRaises(ValueError):
            load_manifest(path)
```

Create `tests/fixtures/manifest-http.json` with the same valid metadata and an `http://` download URL before running the test.

- [ ] **Step 2: Run the tests and verify the expected failures**

Run: `python3 -m unittest tests.test_aof7_installer.ManifestTests -v`  
Expected: FAIL because the manifest model and path functions are not implemented.

- [ ] **Step 3: Implement the smallest validating model**

Use `json`, `dataclasses`, `urllib.parse`, and `pathlib` only. Require a JSON object, `minecraft.version == "1.20.1"`, one loader entry exactly `fabric-0.16.0`, a list of file objects, and a non-empty HTTPS `downloadUrl` for every entry. Normalize each manifest filename to a forward-slash relative path, reject absolute paths, `..` components, NUL bytes, and names outside `mods/`. Deduplicate identical URLs while preserving first occurrence. Make `safe_join` resolve both root and target and require the target to remain below root. Copy overrides with `os.walk`, never follow symlinks, and preserve relative paths under the destination.

- [ ] **Step 4: Run the validation tests and verify they pass**

Run: `python3 -m unittest tests.test_aof7_installer.ManifestTests -v`  
Expected: PASS with four tests.

---

### Task 3: Implement resumable concurrent downloads and install state

**Files:**
- Modify: `windows-kit/aof7_installer.py`
- Modify: `tests/test_aof7_installer.py`

**Interfaces:**
- `sha256_file(path: Path) -> str`.
- `DownloadRecord(url: str, path: str, size: int, sha256: str)`.
- `download_entries(entries: tuple[ManifestEntry, ...], mods_root: Path, state_path: Path, workers: int = 8, attempts: int = 5) -> tuple[DownloadRecord, ...]`.

- [ ] **Step 1: Write failing downloader tests using a local HTTP server**

```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading


class DownloadTests(unittest.TestCase):
    def test_downloads_atomically_and_rerun_skips_verified_file(self):
        payload = b"jar payload"
        server = ThreadingHTTPServer(("127.0.0.1", 0), StaticHandler(payload))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/example.jar"
            entry = ManifestEntry(url, "mods/example.jar", None, None)
            output = self.tempdir / "mods"
            state = self.tempdir / "state.json"
            first = download_entries((entry,), output, state, workers=2)
            second = download_entries((entry,), output, state, workers=2)
            self.assertEqual(first[0].sha256, second[0].sha256)
            self.assertEqual((output / "example.jar").read_bytes(), payload)
            self.assertFalse(list(output.glob("*.part")))
        finally:
            server.shutdown()
```

The local HTTP server is used only by the downloader unit test with a direct `ManifestEntry`; `load_manifest` still rejects HTTP and production downloads keep normal HTTPS certificate verification. Add tests for a pre-existing `.part` file receiving a `Range` request, a `503` response retrying, and a failed replacement leaving the old verified file intact.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python3 -m unittest tests.test_aof7_installer.DownloadTests -v`  
Expected: FAIL because the downloader and state model are not implemented.

- [ ] **Step 3: Implement the downloader with standard-library concurrency**

Use `urllib.request`, `ThreadPoolExecutor(max_workers=min(workers, 8))`, `time.monotonic`, and `random.uniform` for bounded exponential backoff. Use a 20-second connect/read timeout, retry `429`, `500`, `502`, `503`, `504`, and socket resets up to five attempts. If a `.part` file exists, request `Range: bytes=<size>-`; append only for HTTP `206`, otherwise restart the temporary file. Stream in 1 MiB chunks, optionally enforce `Content-Length`, compute SHA-256 while writing, flush and `os.replace` the temporary file. Store state as JSON containing URL, relative path, byte count, and SHA-256. Skip only when the existing file matches the recorded URL, size, and hash. Raise one aggregated `DownloadFailure` after all workers finish, listing each URL and filename.

- [ ] **Step 4: Run the downloader tests and verify they pass**

Run: `python3 -m unittest tests.test_aof7_installer.DownloadTests -v`  
Expected: PASS with atomic, retry, resume, and idempotency coverage.

---

### Task 4: Implement the Python bootstrap and PowerShell orchestration

**Files:**
- Modify: `windows-kit/Install-AOF7.ps1`
- Modify: `windows-kit/aof7_installer.py`
- Modify: `tests/test_aof7_installer.py`

**Interfaces:**
- PowerShell `Get-PythonAsset()` returns a two-field object with `Url` and `Sha256`.
- PowerShell `Install-EmbeddedPython($KitRoot, $OutputRoot)` returns the path to `python.exe`.
- Python `install_pack(manifest_path: Path, kit_root: Path, output_root: Path, workers: int = 8) -> dict` returns `entries`, `downloaded`, `skipped`, `overrides`, and `state_path`.
- Python `main()` supports `--manifest`, `--kit-root`, `--output-root`, `--workers`, `--check-only`, and `--self-test`.

- [ ] **Step 1: Write failing bootstrap and orchestration tests**

```python
import subprocess


class BootstrapTests(unittest.TestCase):
    def test_powershell_pins_all_supported_python_archives(self):
        text = (KIT / "Install-AOF7.ps1").read_text(encoding="utf-8")
        for name in ("embed-amd64", "embed-arm64", "embed-win32"):
            self.assertIn(name, text)
        self.assertIn("4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3", text)

    def test_check_only_reads_manifest_without_creating_mods(self):
        result = subprocess.run(
            [sys.executable, str(KIT / "aof7_installer.py"), "--check-only",
             "--manifest", str(ROOT / "tests/fixtures/manifest-minimal.json")],
            capture_output=True, text=True, check=True,
        )
        self.assertIn('"entries": 1', result.stdout)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m unittest tests.test_aof7_installer.BootstrapTests -v`  
Expected: FAIL because the PowerShell pin table and Python CLI are incomplete.

- [ ] **Step 3: Implement the pinned Python bootstrap**

Add this exact asset table to `Install-AOF7.ps1`:

```powershell
$PythonAssets = @{
    'amd64' = @{ Url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'; Sha256 = '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3' }
    'arm64' = @{ Url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-arm64.zip'; Sha256 = '3065efc3d382d1cda66757ac71ade11904fa6e350f5a97eb74811acd71ba5532' }
    'x86'   = @{ Url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-win32.zip'; Sha256 = '084b9eb24cb848605c895d05b738fbc2572efc8b4c18c415a824065864a2b853' }
}
```

Detect `PROCESSOR_ARCHITECTURE` and `PROCESSOR_ARCHITEW6432`, create `tools\python`, download to a temporary file with `Invoke-WebRequest -UseBasicParsing`, verify `Get-FileHash -Algorithm SHA256`, extract with `Expand-Archive`, and remove the archive only after `python.exe --version` succeeds. Use a named .NET mutex `OnlyBangers.AOF7.2.5.3.Installer` before touching output. Check Windows 10/11, writable Documents, and at least 8 GB free space. Never log URLs containing credentials.

- [ ] **Step 4: Implement the Python CLI orchestration**

Resolve defaults from the script directory and current user's known Documents folder. Create `mods`, `logs`, and `tools/python` under `AOF7-2.5.3`. Write a timestamped log through `logging`, call `load_manifest`, call `download_entries`, copy `overrides`, write `.aof7-install-state.json`, and return nonzero on any required failure. `--check-only` validates versions, entry count, URLs, and paths without creating or downloading output files.

- [ ] **Step 5: Run the bootstrap and CLI tests**

Run: `python3 -m unittest tests.test_aof7_installer.BootstrapTests -v`  
Expected: PASS with the pinned asset and check-only tests.

---

### Task 5: Install Fabric and create the isolated official-launcher profile

**Files:**
- Modify: `windows-kit/Install-AOF7.ps1`
- Modify: `windows-kit/aof7_installer.py`
- Modify: `tests/test_aof7_installer.py`
- Modify: `windows-kit/README.md`

**Interfaces:**
- Python `merge_launcher_profile(profile_path: Path, output_root: Path, profile_name: str = "AOF7 2.5.3") -> None`.
- PowerShell `Install-FabricClient($MinecraftRoot, $OutputRoot, $JavaPath)`.
- PowerShell `Write-LaunchCommand($OutputRoot)`.

- [ ] **Step 1: Write failing launcher-profile tests**

```python
class LauncherProfileTests(unittest.TestCase):
    def test_adds_isolated_profile_without_removing_existing_profiles(self):
        profile_path = self.tempdir / "launcher_profiles.json"
        profile_path.write_text(json.dumps({"profiles": {"existing": {"name": "Keep"}}}), encoding="utf-8")
        merge_launcher_profile(profile_path, self.tempdir / "AOF7-2.5.3")
        data = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertIn("existing", data["profiles"])
        created = data["profiles"]["aof7-2.5.3"]
        self.assertEqual(created["lastVersionId"], "fabric-loader-0.16.0-1.20.1")
        self.assertEqual(created["gameDir"], str(self.tempdir / "AOF7-2.5.3"))

    def test_profile_write_creates_backup(self):
        profile_path = self.tempdir / "launcher_profiles.json"
        profile_path.write_text('{"profiles": {}}', encoding="utf-8")
        merge_launcher_profile(profile_path, self.tempdir / "AOF7-2.5.3")
        self.assertTrue(profile_path.with_suffix(".json.aof7-backup").exists())
```

- [ ] **Step 2: Run the launcher tests and verify they fail**

Run: `python3 -m unittest tests.test_aof7_installer.LauncherProfileTests -v`  
Expected: FAIL because profile merge and backup logic are not implemented.

- [ ] **Step 3: Implement profile merge and backup**

Load existing JSON or start with `{"profiles": {}}`, copy the original to `launcher_profiles.json.aof7-backup` before modification, preserve every existing key, and write a UTF-8 temporary JSON followed by `os.replace`. Add profile id `aof7-2.5.3`, `name: "AOF7 2.5.3"`, `type: "custom"`, `lastVersionId: "fabric-loader-0.16.0-1.20.1"`, and the absolute `gameDir`. Do not store accounts, access tokens, or passwords.

- [ ] **Step 4: Implement Fabric installation in PowerShell**

Use the official installer URL `https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.0/fabric-installer-1.0.0.jar` and SHA-256 `7d7e5b1d3a7f8e2081069898e95dc71d84bb3a5c79cb235c034895173cfd347b`. Locate Java in the official launcher runtime under `%APPDATA%\.minecraft\runtime`, then on `PATH`. Run:

```powershell
& $java -jar $fabricInstaller client -dir $minecraftRoot -mcversion 1.20.1 -loader 0.16.0 -launcher win32
if ($LASTEXITCODE -ne 0) { throw "Fabric installer failed with exit code $LASTEXITCODE" }
```

After the installer returns, call `merge_launcher_profile` with `%APPDATA%\.minecraft\launcher_profiles.json`, verify the `fabric-loader-0.16.0-1.20.1` version directory exists, and write `AOF7-2.5.3-launch.cmd` that starts the official launcher through `start "" "minecraft:"`. Stop before profile changes if Java, the launcher root, or the Fabric installer cannot be verified.

- [ ] **Step 5: Document the final user flow and run launcher tests**

Document official launcher sign-in, selecting `AOF7 2.5.3`, assigning 6–8 GB RAM, and the two server addresses. Run: `python3 -m unittest tests.test_aof7_installer.LauncherProfileTests -v`  
Expected: PASS with profile preservation and backup coverage.

---

### Task 6: Stage the real AOF7 manifest, package the kit, and verify end to end

**Files:**
- Create: `windows-kit/manifest.json`
- Create: `windows-kit/overrides/` copied from the AOF7 client pack
- Modify: `windows-kit/README.md`
- Create: `dist/AOF7-Windows-Kit-2.5.3.zip`

**Interfaces:**
- The distributable kit contains scripts, Python installer, real `manifest.json`, and overrides only; it contains no mod JARs.
- `Install-AOF7.cmd --CheckOnly` validates the real pack without network writes.
- `AOF7-Windows-Kit-2.5.3.zip` is the portable handoff artifact.

- [ ] **Step 1: Add the real AOF7 manifest and overrides**

Copy the verified AOF7 2.5.3 `manifest.json` into `windows-kit/manifest.json` and copy only its `overrides` tree. Confirm the manifest declares Minecraft `1.20.1`, loader `fabric-0.16.0`, and 436 file entries. Do not copy the downloaded `mods` directory into the kit.

- [ ] **Step 2: Add the real-manifest validation test**

```python
class RealPackTests(unittest.TestCase):
    def test_real_pack_manifest_is_complete(self):
        pack = load_manifest(ROOT / "windows-kit/manifest.json")
        self.assertEqual(pack.minecraft_version, "1.20.1")
        self.assertEqual(pack.loader_version, "0.16.0")
        self.assertEqual(len(pack.entries), 436)
        self.assertTrue(all(entry.url.startswith("https://") for entry in pack.entries))
```

- [ ] **Step 3: Run local static and manifest verification**

Run: `python3 -m py_compile windows-kit/aof7_installer.py`  
Expected: exit 0.

Run: `python3 -m unittest -v`  
Expected: all tests pass.

Run: `python3 windows-kit/aof7_installer.py --check-only --manifest windows-kit/manifest.json`  
Expected: JSON reports `minecraft=1.20.1`, `loader=0.16.0`, `entries=436`, and no output downloads.

- [ ] **Step 4: Package without third-party binaries**

Create `dist/AOF7-Windows-Kit-2.5.3.zip` from `windows-kit`, excluding `mods`, `tools/python`, logs, `.part`, and state files. List the archive and assert it contains `Install-AOF7.cmd`, `Install-AOF7.ps1`, `aof7_installer.py`, `manifest.json`, and `overrides/`, while containing no `*.jar`.

- [ ] **Step 5: Attempt the requested Windows Documents handoff**

If `/mnt/c/Users/vgreis/Documents` exists and is writable, copy the complete kit folder and ZIP to `/mnt/c/Users/vgreis/Documents/AOF7-Windows-Kit-2.5.3`; otherwise leave the verified artifact in `dist/` and report the exact path for copying to Windows. Never write outside the detected Documents directory.

- [ ] **Step 6: Perform final verification before handoff**

Run: `python3 -m unittest -v` and `python3 windows-kit/aof7_installer.py --self-test`  
Expected: zero failures and `aof7-installer self-test: ok`.

Run: `unzip -l dist/AOF7-Windows-Kit-2.5.3.zip`  
Expected: kit files present, no mod JARs, no credentials, and no temporary state.

Record the final artifact path, SHA-256, supported Windows architectures, and the required first-run action: sign into the official Minecraft Launcher before launching the created Fabric profile.
