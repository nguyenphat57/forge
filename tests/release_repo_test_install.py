from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport, build_release, install_bundle


def assert_is_relative_to(test_case: ReleaseRepoTestSupport, path: str | Path, parent: Path) -> None:
    test_case.assertTrue(Path(path).resolve().is_relative_to(parent.resolve()))


def assert_is_not_relative_to(test_case: ReleaseRepoTestSupport, path: str | Path, parent: Path) -> None:
    test_case.assertFalse(Path(path).resolve().is_relative_to(parent.resolve()))


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
                dry_run=True,
            )

            self.assertTrue((target / "marker.txt").exists())
            self.assertEqual(report["bundle"], "forge-codex")
            self.assertIsNotNone(report["backup_path"])
            self.assertFalse(Path(report["backup_path"]).exists())
            assert_is_relative_to(
                self,
                report["backup_path"],
                temp_root / "runtime" / "forge-codex-state" / "rollbacks" / "install",
            )
            assert_is_not_relative_to(self, report["backup_path"], ROOT_DIR)

    def test_install_bundle_rejects_retired_bundle_names(self) -> None:
        for bundle_name in ("forge-browse", "forge-design", "forge-nextjs-typescript-postgres"):
            with self.subTest(bundle=bundle_name):
                with self.assertRaises(KeyError):
                    install_bundle.install_bundle(bundle_name, dry_run=True)

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
            )

            self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((target / "old.txt").exists())
            self.assertIsNotNone(report["backup_path"])
            self.assertTrue(Path(report["backup_path"]).exists())
            assert_is_relative_to(
                self,
                report["backup_path"],
                temp_root / "runtime" / "forge-antigravity-state" / "rollbacks" / "install",
            )
            assert_is_not_relative_to(self, report["backup_path"], ROOT_DIR)

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
            self.assertTrue(manifest["bundle_fingerprint"]["matches_source"])
            self.assertFalse(manifest["bundle_fingerprint"]["host_mutation_expected"])
            self.assertEqual(
                manifest["bundle_fingerprint"]["source"]["sha256"],
                report["source_build_manifest"]["bundle_fingerprint"]["sha256"],
            )
            self.assertEqual(
                manifest["bundle_fingerprint"]["installed"]["sha256"],
                report["source_build_manifest"]["bundle_fingerprint"]["sha256"],
            )

    def test_installed_codex_bundle_uses_codex_host_state_by_default(self) -> None:
        build_release.build_all()
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex-home"
            target = codex_home / "skills" / "forge-codex"
            target.mkdir(parents=True, exist_ok=True)

            install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                activate_codex=True,
                codex_home=str(codex_home),
            )

            workspace = temp_root / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            expected_state_root = (codex_home / "forge-codex").resolve()
            expected_preferences = (expected_state_root / "state" / "preferences.json").resolve()
            env = os.environ.copy()
            env.pop("FORGE_HOME", None)

            write_result = subprocess.run(
                [
                    sys.executable,
                    str(target / "scripts" / "write_preferences.py"),
                    "--workspace",
                    str(workspace),
                    "--technical-level",
                    "technical",
                    "--apply",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                env=env,
            )
            self.assertEqual(write_result.returncode, 0, write_result.stderr)
            write_report = json.loads(write_result.stdout)

            self.assertEqual(write_report["state_root"], str(expected_state_root))
            self.assertEqual(write_report["targets"], [str(expected_preferences)])
            self.assertTrue(expected_preferences.exists())


if __name__ == "__main__":
    import unittest

    unittest.main()
