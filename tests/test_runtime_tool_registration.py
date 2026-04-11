from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import build_release
import install_bundle


ROOT_DIR = Path(__file__).resolve().parents[1]


class InstallManifestContractTests(unittest.TestCase):
    def test_install_manifest_omits_retired_registration_fields(self) -> None:
        build_release.build_all(force=True)
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_target = temp_root / "runtime" / "forge-codex"
            antigravity_target = temp_root / "runtime" / "forge-antigravity"

            install_bundle.install_bundle("forge-codex", target=str(codex_target), backup_dir=str(temp_root / "backups"))
            install_bundle.install_bundle(
                "forge-antigravity",
                target=str(antigravity_target),
                backup_dir=str(temp_root / "backups"),
            )

            codex_manifest = json.loads((codex_target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            antigravity_manifest = json.loads((antigravity_target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))

            for manifest in (codex_manifest, antigravity_manifest):
                with self.subTest(bundle=manifest["bundle"]):
                    self.assertNotIn("codex_runtime_registration", manifest)
                    self.assertNotIn("gemini_runtime_registration", manifest)
                    self.assertNotIn("codex_companion_registration", manifest)
                    self.assertNotIn("gemini_companion_registration", manifest)

    def test_build_release_does_not_ship_retired_bundle_directories(self) -> None:
        build_release.build_all(force=True)
        for bundle_name in ("forge-browse", "forge-design", "forge-nextjs-typescript-postgres"):
            with self.subTest(bundle=bundle_name):
                self.assertFalse((ROOT_DIR / "dist" / bundle_name).exists())


if __name__ == "__main__":
    unittest.main()
