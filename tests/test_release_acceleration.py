from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402
import verify_repo  # noqa: E402


class ReleaseAccelerationTests(unittest.TestCase):
    def test_verify_repo_fast_profile_stays_targeted(self) -> None:
        step_names = [name for name, _, _ in verify_repo.build_step_specs("fast")]

        self.assertIn("repo.generated_host_artifacts", step_names)
        self.assertIn("forge-core.unittest.fast.contracts", step_names)
        self.assertNotIn("build_release", step_names)
        self.assertFalse(any(name.startswith("dist.") for name in step_names))

    def test_verify_repo_full_profile_keeps_release_steps(self) -> None:
        step_names = [name for name, _, _ in verify_repo.build_step_specs("full")]

        self.assertIn("build_release", step_names)
        self.assertIn("install_dry_run.forge-browse", step_names)
        self.assertTrue(any(name.startswith("dist.") for name in step_names))

    def test_repeated_build_release_skips_when_inputs_match(self) -> None:
        build_release.build_all(force=True)
        outputs = build_release.build_all()

        self.assertTrue(outputs)
        self.assertTrue(all(item.get("skipped") for item in outputs))
        for item in outputs:
            manifest = json.loads((Path(item["path"]) / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
            with self.subTest(bundle=item["name"]):
                self.assertIn("source_input_fingerprint", manifest)
                self.assertEqual(manifest["source_input_fingerprint"]["mode"], "path-set-content-sha256-v1")

    def test_install_bundle_skips_sync_when_target_matches_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = temp_root / "runtime" / "forge-codex"
            backups = temp_root / "backups"

            first_report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                backup_dir=str(backups),
            )
            second_report = install_bundle.install_bundle(
                "forge-codex",
                target=str(target),
                backup_dir=str(backups),
            )

            self.assertTrue(first_report["bundle_sync_required"])
            self.assertFalse(second_report["bundle_sync_required"])
            self.assertFalse(second_report["backup_enabled"])
            self.assertIsNone(second_report["backup_path"])
            self.assertEqual(second_report["transition"]["status"], "already-current")
            self.assertTrue(second_report["bundle_fingerprint"]["matches_source"])


if __name__ == "__main__":
    unittest.main()
