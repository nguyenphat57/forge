from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script, workspace_fixture


class HelpNextWorkflowStateTests(unittest.TestCase):
    def test_next_prefers_workflow_state_when_execution_is_review_ready(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")

            progress = run_python_script(
                "track_execution_progress.py",
                "Offline reconciliation",
                "--mode",
                "checkpoint-batch",
                "--stage",
                "integration",
                "--status",
                "completed",
                "--completion-state",
                "ready-for-review",
                "--proof",
                "pytest tests/test_reconciliation.py",
                "--next",
                "Run merge readiness pass",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(progress.returncode, 0, progress.stderr)

            result = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["current_stage"], "review-ready")
        self.assertEqual(report["suggested_workflow"], "review")
        self.assertEqual(report["current_focus"], "Review ready: Offline reconciliation")
        self.assertIn("workflow-state", " ".join(report["evidence"]))
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")

    def test_next_uses_blocked_quality_gate_when_it_is_last_recorded(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")

            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Checkout rollback slice",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--profile",
                "standard",
                "--target-claim",
                "ready-for-merge",
                "--decision",
                "blocked",
                "--evidence",
                "pytest tests/test_checkout.py",
                "--response",
                "I verified: checkout regression suite is still failing. Correct because the fix is not complete. Fixed: no.",
                "--why",
                "Checkout regression is still failing on the offline retry path.",
                "--next-evidence",
                "Re-run checkout regression after fixing offline retry state",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)

            result = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["current_stage"], "blocked")
        self.assertEqual(report["suggested_workflow"], "debug")
        self.assertEqual(report["current_focus"], "Gate blocked: ready-for-merge")
        self.assertIn("Next evidence needed", report["recommended_action"])

    def test_next_prefers_gate_approval_over_previous_run_result(self) -> None:
        helper = Path(workspace_fixture("run_workspace")).parents[1] / "run_helpers" / "build_fixture.py"
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")

            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Deploy readiness slice",
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

            run_result = run_python_script(
                "run_with_guidance.py",
                "--workspace",
                str(workspace_fixture("run_workspace")),
                "--project-name",
                "Example Project",
                "--timeout-ms",
                "1000",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
                "--",
                "python",
                str(helper),
            )
            self.assertEqual(run_result.returncode, 0, run_result.stderr)

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--profile",
                "standard",
                "--target-claim",
                "deploy",
                "--decision",
                "go",
                "--evidence",
                "python scripts/build_release.py --format json",
                "--response",
                "I verified: release bundle build passed. Correct because the bundle rendered cleanly. Fixed: yes.",
                "--why",
                "Build and review evidence are fresh enough for the deploy handoff.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)

            result = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["suggested_workflow"], "deploy")
        self.assertEqual(report["current_focus"], "Gate approved: deploy")


if __name__ == "__main__":
    unittest.main()
