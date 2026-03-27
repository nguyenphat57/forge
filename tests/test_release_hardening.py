from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402


class ReleaseHardeningTests(unittest.TestCase):
    def test_build_release_excludes_cached_python_artifacts(self) -> None:
        build_release.build_all()
        for bundle_name in ("forge-antigravity", "forge-codex"):
            with self.subTest(bundle=bundle_name):
                dist_root = ROOT_DIR / "dist" / bundle_name
                self.assertFalse(any(dist_root.rglob("__pycache__")))
                self.assertFalse(any(dist_root.rglob("*.pyc")))

    def test_install_bundle_rejects_repo_local_targets(self) -> None:
        build_release.build_all()
        targets = [
            ROOT_DIR / ".tmp" / "repo-target",
            ROOT_DIR / "dist" / "repo-target",
            ROOT_DIR / "packages" / "repo-target",
        ]
        for target in targets:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    install_bundle.install_bundle(
                        "forge-codex",
                        target=str(target),
                        dry_run=True,
                    )

    def test_repeated_build_release_remains_stable_after_dist_execution(self) -> None:
        build_release.build_all()
        verify_script = ROOT_DIR / "dist" / "forge-codex" / "scripts" / "verify_bundle.py"
        result = subprocess.run(
            [sys.executable, str(verify_script), "--format", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")

        build_release.build_all()
        self.assertTrue((ROOT_DIR / "dist" / "forge-antigravity" / "BUILD-MANIFEST.json").exists())
        self.assertTrue((ROOT_DIR / "dist" / "forge-codex" / "BUILD-MANIFEST.json").exists())

    def test_verify_repo_pipeline_includes_secret_scan(self) -> None:
        verify_repo = (ROOT_DIR / "scripts" / "verify_repo.py").read_text(encoding="utf-8")
        self.assertIn("repo.secret_scan", verify_repo)
        self.assertTrue((ROOT_DIR / "scripts" / "scan_repo_secrets.py").exists())


if __name__ == "__main__":
    unittest.main()
