from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


RECORD_REVIEW_STATE = Path(__file__).resolve().parents[1] / "scripts" / "record_review_state.py"


@unittest.skipUnless(RECORD_REVIEW_STATE.exists(), "record_review_state.py is not present yet.")
class ReviewStateTests(unittest.TestCase):
    def test_review_state_round_trip_records_workflow_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Review Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"review-workspace"}\n', encoding="utf-8")

            result = run_python_script(
                "record_review_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--scope",
                "Checkout slice",
                "--review-kind",
                "merge-readiness",
                "--disposition",
                "ready-for-merge",
                "--branch-state",
                "clean",
                "--evidence",
                "pytest tests/test_checkout.py",
                "--no-finding-rationale",
                "No findings in the reviewed slice.",
                "--next-action",
                "Run merge readiness smoke",
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
        self.assertEqual(state["last_recorded_kind"], "review-state")
        self.assertEqual(state["latest_review"]["kind"], "review-state")
        self.assertEqual(state["summary"]["suggested_workflow"], "quality-gate")


if __name__ == "__main__":
    unittest.main()
