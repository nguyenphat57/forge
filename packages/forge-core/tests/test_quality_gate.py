from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class QualityGateTests(unittest.TestCase):
    def test_release_critical_deploy_rejects_conditional_decision(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Release candidate\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"release-candidate"}\n', encoding="utf-8")

            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Release candidate hardening",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)

            review_pack = run_python_script(
                "review_pack.py",
                "--workspace",
                str(workspace),
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertIn(review_pack.returncode, {0, 1}, review_pack.stderr)

            result = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--profile",
                "release-critical",
                "--target-claim",
                "deploy",
                "--decision",
                "conditional",
                "--evidence",
                "python scripts/build_release.py --format json",
                "--response",
                "I verified: release bundle build passed. Correct because the bundle rendered cleanly. Fixed: yes.",
                "--why",
                "The release still needs one more smoke pass.",
                "--next-evidence",
                "Run release smoke on production-like target",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("cannot be conditional", report["error"])

    def test_persisted_quality_gate_writes_workflow_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Checkout review slice",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)

            result = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--profile",
                "standard",
                "--target-claim",
                "ready-for-review",
                "--decision",
                "go",
                "--evidence",
                "pytest tests/test_checkout.py",
                "--response",
                "I verified: checkout regression passed. Correct because the retry path now stays stable. Fixed: yes.",
                "--why",
                "Fresh verification is strong enough for review handoff.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            state_path = workspace / ".forge-artifacts" / "workflow-state" / "example-project" / "latest.json"
            self.assertTrue(state_path.exists())
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(state["latest_gate"]["decision"], "go")
        self.assertEqual(state["summary"]["suggested_workflow"], "review")


if __name__ == "__main__":
    unittest.main()
