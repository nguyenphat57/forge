from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class VerifyChangeTests(unittest.TestCase):
    def test_verify_change_persists_pass_report_for_complete_active_change(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Stabilize checkout retry",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            slug = json.loads(started.stdout)["change"]["slug"]

            updated = run_python_script(
                "change_artifacts.py",
                "status",
                "--workspace",
                str(workspace),
                "--slug",
                slug,
                "--state",
                "ready-for-review",
                "--verified",
                "pytest tests/test_checkout_retry.py",
                "--format",
                "json",
            )
            self.assertEqual(updated.returncode, 0, updated.stderr)

            verified = run_python_script(
                "verify_change.py",
                "--workspace",
                str(workspace),
                "--slug",
                slug,
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )

            self.assertEqual(verified.returncode, 0, verified.stderr)
            report = json.loads(verified.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(Path(report["artifacts"]["json"]).exists())
            self.assertEqual(report["scores"]["completeness"], 100)

    def test_verify_change_fails_when_spec_delta_is_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Adjust checkout capture",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            report = json.loads(started.stdout)
            slug = report["change"]["slug"]
            Path(report["paths"]["spec"]).unlink()

            verified = run_python_script(
                "verify_change.py",
                "--workspace",
                str(workspace),
                "--slug",
                slug,
                "--format",
                "json",
            )

            self.assertEqual(verified.returncode, 1)
            payload = json.loads(verified.stdout)
            self.assertEqual(payload["status"], "FAIL")
            self.assertIn("specs", payload["missing_artifacts"])


if __name__ == "__main__":
    unittest.main()
