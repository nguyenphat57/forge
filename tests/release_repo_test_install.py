from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ReleaseRepoTestSupport, build_release, install_bundle


class ReleaseRepoInstallTests(ReleaseRepoTestSupport):
    def test_install_bundle_dry_run_keeps_target_untouched(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-codex"
            target.mkdir(parents=True, exist_ok=True)
            (target / "marker.txt").write_text("keep", encoding="utf-8")

            report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                backup_dir=str(temp_root / "backups"),
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
            self.assertEqual(manifest["state"]["scope"], "adapter-global")
            self.assertEqual(
                manifest["state"]["root"],
                str((temp_root / "runtime" / "forge-antigravity-state").resolve()),
            )
            self.assertEqual(
                manifest["state"]["preferences_path"],
                str((temp_root / "runtime" / "forge-antigravity-state" / "state" / "preferences.json").resolve()),
            )
            self.assertTrue((temp_root / "runtime" / "forge-antigravity-state").is_dir())
            self.assertTrue((temp_root / "runtime" / "forge-antigravity-state" / "state").is_dir())

    def test_install_bundle_succeeds_when_target_root_is_locked_as_cwd(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-antigravity"
            target.mkdir(parents=True, exist_ok=True)
            (target / "old.txt").write_text("old", encoding="utf-8")

            locker = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import os, sys, time; os.chdir(sys.argv[1]); time.sleep(10)",
                    str(target),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            try:
                report = install_bundle.install_bundle(
                    "forge-antigravity",
                    target=str(target),
                    backup_dir=str(temp_root / "backups"),
                )
            finally:
                locker.terminate()
                locker.wait(timeout=5)

            self.assertEqual(report["bundle"], "forge-antigravity")
            self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((target / "old.txt").exists())
