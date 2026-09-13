from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).parents[1]
KIT = ROOT / "windows-kit"
sys.path.insert(0, str(KIT))

from aof7_installer import (  # noqa: E402
    ManifestEntry,
    download_entries,
    load_manifest,
    merge_launcher_profile,
    safe_join,
)


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

    def test_rejects_url_credentials(self):
        data = json.loads((ROOT / "tests/fixtures/manifest-minimal.json").read_text(encoding="utf-8"))
        data["files"][0]["downloadUrl"] = "https://user:password@example.com/example.jar"
        path = Path(tempfile.mkstemp(prefix="aof7-credentials-", suffix=".json")[1])
        try:
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)
        finally:
            path.unlink(missing_ok=True)


class _StaticHandler(BaseHTTPRequestHandler):
    payload = b"jar payload"
    failures = 0
    ranges = []

    def do_GET(self):  # noqa: N802
        if type(self).failures:
            type(self).failures -= 1
            self.send_error(503)
            return
        payload = type(self).payload
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            start = int(range_header.removeprefix("bytes=").split("-", 1)[0])
            type(self).ranges.append(start)
            payload = payload[start:]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(type(self).payload) - 1}/{len(type(self).payload)}")
        else:
            self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        return


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aof7-test-"))

    def tearDown(self):
        for path in sorted(self.tempdir.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        self.tempdir.rmdir()

    def _server(self, payload=b"jar payload", failures=0):
        _StaticHandler.payload = payload
        _StaticHandler.failures = failures
        _StaticHandler.ranges = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), _StaticHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server

    def test_downloads_atomically_and_rerun_skips_verified_file(self):
        server = self._server()
        try:
            url = f"http://127.0.0.1:{server.server_port}/example.jar"
            entry = ManifestEntry(url, "mods/example.jar", None, None)
            output = self.tempdir / "mods"
            state = self.tempdir / "state.json"
            first = download_entries((entry,), output, state, workers=2)
            second = download_entries((entry,), output, state, workers=2)
            self.assertEqual(first[0].sha256, second[0].sha256)
            self.assertEqual((output / "example.jar").read_bytes(), b"jar payload")
            self.assertFalse(list(output.glob("*.part")))
        finally:
            server.shutdown()
            server.server_close()

    def test_resumes_preexisting_part_with_range(self):
        payload = b"resumable payload"
        server = self._server(payload)
        try:
            url = f"http://127.0.0.1:{server.server_port}/resume.jar"
            output = self.tempdir / "mods"
            output.mkdir()
            (output / "resume.jar.part").write_bytes(payload[:5])
            record = download_entries(
                (ManifestEntry(url, "mods/resume.jar", None, None),),
                output,
                self.tempdir / "state.json",
            )[0]
            self.assertEqual((output / "resume.jar").read_bytes(), payload)
            self.assertEqual(record.size, len(payload))
            self.assertEqual(_StaticHandler.ranges, [5])
        finally:
            server.shutdown()
            server.server_close()

    def test_retries_transient_503(self):
        server = self._server(b"retry payload", failures=2)
        try:
            url = f"http://127.0.0.1:{server.server_port}/retry.jar"
            records = download_entries(
                (ManifestEntry(url, "mods/retry.jar", None, None),),
                self.tempdir / "mods",
                self.tempdir / "state.json",
                attempts=3,
            )
            self.assertEqual(records[0].size, len(b"retry payload"))
        finally:
            server.shutdown()
            server.server_close()

    def test_encodes_spaces_in_download_url(self):
        server = self._server(b"space payload")
        try:
            url = f"http://127.0.0.1:{server.server_port}/file with space.jar"
            records = download_entries(
                (ManifestEntry(url, "mods/space.jar", None, None),),
                self.tempdir / "mods",
                self.tempdir / "state.json",
            )
            self.assertEqual(records[0].size, len(b"space payload"))
        finally:
            server.shutdown()
            server.server_close()

    def test_failed_replacement_keeps_old_file(self):
        old_payload = b"verified old payload"
        output = self.tempdir / "mods"
        output.mkdir()
        target = output / "same.jar"
        target.write_bytes(old_payload)
        state = self.tempdir / "state.json"
        state.write_text(json.dumps({"files": [{
            "url": "https://old.example/same.jar",
            "path": "mods/same.jar",
            "size": len(old_payload),
            "sha256": hashlib.sha256(old_payload).hexdigest(),
        }]}), encoding="utf-8")
        server = self._server(failures=5)
        try:
            url = f"http://127.0.0.1:{server.server_port}/same.jar"
            with self.assertRaises(Exception):
                download_entries(
                    (ManifestEntry(url, "mods/same.jar", None, None),),
                    output,
                    state,
                    attempts=2,
                )
            self.assertEqual(target.read_bytes(), old_payload)
            self.assertFalse((output / "same.jar.part").exists())
        finally:
            server.shutdown()
            server.server_close()


class BootstrapTests(unittest.TestCase):
    def test_powershell_pins_all_supported_python_archives(self):
        text = (KIT / "Install-AOF7.ps1").read_text(encoding="utf-8")
        for name in ("embed-amd64", "embed-arm64", "embed-win32"):
            self.assertIn(name, text)
        self.assertIn("4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3", text)

    def test_cmd_accepts_double_dash_check_only(self):
        text = (KIT / "Install-AOF7.ps1").read_text(encoding="utf-8")
        self.assertIn("RemainingArguments", text)
        self.assertIn("--CheckOnly", text)

    def test_powershell_creates_empty_profile_file_when_missing(self):
        text = (KIT / "Install-AOF7.ps1").read_text(encoding="utf-8")
        self.assertIn("$emptyProfiles = '{\"profiles\":{}}'", text)
        self.assertIn("[IO.File]::WriteAllText", text)

    def test_check_only_reads_manifest_without_creating_mods(self):
        output = Path(tempfile.mkdtemp(prefix="aof7-check-"))
        try:
            result = subprocess.run(
                [sys.executable, str(KIT / "aof7_installer.py"), "--check-only",
                 "--manifest", str(ROOT / "tests/fixtures/manifest-minimal.json"),
                 "--output-root", str(output)],
                capture_output=True, text=True, check=True,
            )
            self.assertIn('"entries": 1', result.stdout)
            self.assertFalse((output / "mods").exists())
        finally:
            output.rmdir()


    def test_powershell_writes_diagnostic_transcript(self):
        text = (KIT / "Install-AOF7.ps1").read_text(encoding="utf-8")
        self.assertIn("Start-Transcript", text)
        self.assertIn("logs\\install.log", text)
        self.assertIn("Stop-Transcript", text)


class LauncherProfileTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aof7-profile-"))

    def tearDown(self):
        for path in sorted(self.tempdir.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        self.tempdir.rmdir()

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


class RealPackTests(unittest.TestCase):
    def test_real_pack_manifest_is_complete(self):
        pack = load_manifest(ROOT / "windows-kit/manifest.json")
        self.assertEqual(pack.minecraft_version, "1.20.1")
        self.assertEqual(pack.loader_version, "0.16.0")
        self.assertEqual(len(pack.entries), 436)
        self.assertTrue(all(entry.url.startswith("https://") for entry in pack.entries))


if __name__ == "__main__":
    unittest.main()
