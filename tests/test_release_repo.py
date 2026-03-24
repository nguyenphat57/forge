from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402


class ReleaseRepoTests(unittest.TestCase):
    def test_release_docs_and_version_exist(self) -> None:
        version = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertTrue((ROOT_DIR / "CHANGELOG.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "architecture" / "adapter-boundary.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "release" / "install.md").exists())
        self.assertTrue((ROOT_DIR / "docs" / "release" / "release-process.md").exists())

    def test_architecture_docs_enforce_core_purity(self) -> None:
        boundary = (ROOT_DIR / "docs" / "architecture" / "adapter-boundary.md").read_text(encoding="utf-8")
        monorepo = (ROOT_DIR / "docs" / "architecture" / "monorepo.md").read_text(encoding="utf-8")
        release_process = (ROOT_DIR / "docs" / "release" / "release-process.md").read_text(encoding="utf-8")

        self.assertIn("forge-claude", boundary)
        self.assertIn("forge-core", boundary)
        self.assertIn("adapter-boundary.md", monorepo)
        self.assertIn("forge-claude", release_process)
        self.assertIn("core purity", release_process.lower())

    def test_build_release_manifest_carries_version(self) -> None:
        build_release.build_all()
        manifest = json.loads((ROOT_DIR / "dist" / "forge-core" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], build_release.read_version())
        self.assertEqual(manifest["package"], "forge-core")
        self.assertIn("git_revision", manifest)

    def test_install_bundle_dry_run_keeps_target_untouched(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "runtime" / "forge-codex"
            target.mkdir(parents=True, exist_ok=True)
            (target / "marker.txt").write_text("keep", encoding="utf-8")

            report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                dry_run=True,
            )

            self.assertTrue((target / "marker.txt").exists())
            self.assertEqual(report["bundle"], "forge-codex")
            self.assertIsNotNone(report["backup_path"])
            self.assertFalse(Path(report["backup_path"]).exists())

    def test_install_bundle_replaces_target_and_writes_manifest(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-antigravity"
            target.mkdir(parents=True, exist_ok=True)
            (target / "old.txt").write_text("old", encoding="utf-8")

            report = install_bundle.install_bundle(
                "forge-antigravity",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
            )

            self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((target / "old.txt").exists())
            self.assertIsNotNone(report["backup_path"])
            self.assertTrue(Path(report["backup_path"]).exists())

            manifest = json.loads((target / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bundle"], "forge-antigravity")
            self.assertEqual(manifest["version"], build_release.read_version())


if __name__ == "__main__":
    unittest.main()
