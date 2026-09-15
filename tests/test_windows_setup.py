import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "windows-kit" / "Install-OnlyBangers.ps1"
GUIDE = ROOT / "docs" / "SETUP-WINDOWS-TLAUNCHER.md"
MANIFEST = ROOT / "windows-kit" / "onlybangers-client-manifest.json"


class WindowsSetupContractTests(unittest.TestCase):
    def test_setup_files_target_current_server(self):
        script = SCRIPT.read_text(encoding="utf-8")
        guide = GUIDE.read_text(encoding="utf-8")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

        self.assertIn("1.20.1", script)
        self.assertIn("0.19.5", script)
        self.assertIn("Get-FileHash", script)
        self.assertIn("schmidt-flowers.tun.ply.gg", script)
        self.assertIn("jei", script.lower())
        self.assertIn("easyauth", script.lower())
        self.assertIn("TLauncher", guide)
        self.assertIn("0.19.5", guide)
        self.assertIn("schmidt-flowers.tun.ply.gg", guide)
        self.assertNotIn("jei", {item["id"].lower() for item in manifest["mods"]})
        self.assertNotIn("easyauth", {item["id"].lower() for item in manifest["mods"]})

    def test_manifest_has_hash_for_every_client_mod(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["minecraft"], "1.20.1")
        self.assertEqual(manifest["fabric_loader"], "0.19.5")
        self.assertEqual(len(manifest["mods"]), 52)
        for mod in manifest["mods"]:
            self.assertRegex(mod["sha512"], r"^[0-9a-f]{128}$")
            self.assertTrue(mod["file"].endswith(".jar"))


if __name__ == "__main__":
    unittest.main()
