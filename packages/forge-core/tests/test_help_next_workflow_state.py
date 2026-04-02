from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import build_route_args, run_python_script, workspace_fixture

import route_preview  # noqa: E402


class HelpNextWorkflowStateTests(unittest.TestCase):
    def test_next_uses_route_preview_seeded_workflow_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")

            report = route_preview.build_report(
                build_route_args("Deploy the app to external users with a public launch")
            )
            route_preview.persist_report(report, str(workspace))

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
        self.assertEqual(report["current_stage"], "change-active")
        self.assertEqual(report["suggested_workflow"], "review-pack")
        self.assertEqual(report["current_focus"], "Recorded workflow stage: review-pack")
        self.assertEqual(
            report["recommended_action"],
            "Resume the recorded workflow stage 'review-pack' before opening new scope.",
        )
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")
        self.assertEqual(report["signals"]["workflow_summary"]["primary_kind"], "route-preview")

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
        self.assertEqual(report["current_focus"], "Review ready: Offline reconciliation [offline-reconciliation]")
        self.assertIn("workflow-state", " ".join(report["evidence"]))
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")

    def test_next_normalizes_legacy_execution_summary_to_valid_workflow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            state_dir = workspace / ".forge-artifacts" / "workflow-state" / "workflow-workspace"
            state_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")
            (state_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "project": "Workflow Workspace",
                        "current_stage": "integration",
                        "last_recorded_kind": "execution-progress",
                        "latest_execution": {
                            "kind": "execution-progress",
                            "label": "Offline reconciliation",
                            "packet_id": "packet-reconciliation",
                            "status": "active",
                            "current_stage": "integration",
                            "completion_state": "in-progress",
                            "next_steps": ["Run integration verification"],
                            "blockers": [],
                            "residual_risk": [],
                        },
                        "summary": {
                            "status": "active",
                            "primary_kind": "execution-progress",
                            "current_focus": "Build packet: Offline reconciliation [packet-reconciliation]",
                            "current_stage": "integration",
                            "suggested_workflow": "integration",
                            "recommended_action": "Continue the active execution slice.",
                            "alternatives": [],
                        },
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

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
        self.assertEqual(report["suggested_workflow"], "build")
        self.assertEqual(report["current_focus"], "Build packet: Offline reconciliation [packet-reconciliation]")
        self.assertEqual(report["signals"]["workflow_summary"]["suggested_workflow"], "build")

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

            updated = run_python_script(
                "change_artifacts.py",
                "status",
                "--workspace",
                str(workspace),
                "--slug",
                "deploy-readiness-slice",
                "--state",
                "ready-for-review",
                "--verified",
                "python scripts/build_release.py --format json",
                "--format",
                "json",
            )
            self.assertEqual(updated.returncode, 0, updated.stderr)

            verify_change = run_python_script(
                "verify_change.py",
                "--workspace",
                str(workspace),
                "--slug",
                "deploy-readiness-slice",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(verify_change.returncode, 0, verify_change.stderr)

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
