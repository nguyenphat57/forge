from __future__ import annotations

import json
import os
import subprocess
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script, workspace_fixture


class HelpNextTests(unittest.TestCase):
    def test_help_uses_session_pending_task_and_preferences(self) -> None:
        result = run_python_script(
            "resolve_help_next.py",
            "--workspace",
            str(workspace_fixture("help_next_session_workspace")),
            "--mode",
            "help",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["suggested_workflow"], "session")
        self.assertEqual(report["current_focus"], "Session task: Finish loyalty verification matrix")
        self.assertEqual(
            report["recommended_action"],
            "Resume the highest-priority pending task: Write migration verification notes.",
        )
        self.assertEqual(report["response_style"]["teaching_mode"], "explain-why")

    def test_next_prefers_latest_plan_when_no_session_exists(self) -> None:
        result = run_python_script(
            "resolve_help_next.py",
            "--workspace",
            str(workspace_fixture("help_next_planned_workspace")),
            "--mode",
            "next",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["current_stage"], "planned")
        self.assertEqual(report["suggested_workflow"], "plan")
        self.assertEqual(report["current_focus"], "Plan: Checkout Rollout")
        self.assertEqual(report["recommended_action"], "Start the first concrete slice from plan 'Checkout Rollout'.")

    def test_help_warns_when_repo_has_no_strong_context(self) -> None:
        result = run_python_script(
            "resolve_help_next.py",
            "--workspace",
            str(workspace_fixture("help_next_unscoped_workspace")),
            "--mode",
            "help",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "WARN")
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["suggested_workflow"], "review")
        self.assertTrue(any("No active plan" in warning for warning in report["warnings"]))

    def test_next_detects_git_changes_and_recommends_verification(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
            (workspace / "README.md").write_text("# Temp Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"temp-workspace"}\n', encoding="utf-8")
            (workspace / "src").mkdir()
            (workspace / "src" / "feature.ts").write_text("export const value = 1;\n", encoding="utf-8")

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

        self.assertEqual(report["current_stage"], "active-changes")
        self.assertEqual(report["suggested_workflow"], "review")
        self.assertIn("run the nearest verification", report["recommended_action"])
        self.assertIn("README.md", report["signals"]["untracked_files"])

    def test_next_detects_git_changes_from_nested_workspace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            nested_workspace = repo_root / "packages" / "forge-core"
            nested_workspace.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True, encoding="utf-8")
            (nested_workspace / "README.md").write_text("# Nested Workspace\n", encoding="utf-8")
            (nested_workspace / "package.json").write_text('{"name":"nested-workspace"}\n', encoding="utf-8")
            (nested_workspace / "src").mkdir()
            (nested_workspace / "src" / "feature.ts").write_text("export const value = 1;\n", encoding="utf-8")

            result = run_python_script(
                "resolve_help_next.py",
                "--workspace",
                str(nested_workspace),
                "--mode",
                "next",
                "--format",
                "json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["current_stage"], "active-changes")
        self.assertEqual(report["suggested_workflow"], "review")
        self.assertIn("README.md", report["signals"]["untracked_files"])

    def test_next_uses_latest_nested_plan_by_mtime(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plans_dir = workspace / "docs" / "plans"
            nested_dir = plans_dir / "nested"
            nested_dir.mkdir(parents=True)
            older_plan = plans_dir / "older.md"
            newer_plan = nested_dir / "newer.md"
            older_plan.write_text("# Plan: Older Slice\n", encoding="utf-8")
            newer_plan.write_text("# Plan: Newer Slice\n", encoding="utf-8")

            older_time = time.time() - 120
            newer_time = time.time()
            os.utime(older_plan, (older_time, older_time))
            os.utime(newer_plan, (newer_time, newer_time))

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

        self.assertEqual(report["current_stage"], "planned")
        self.assertEqual(report["signals"]["latest_plan_title"], "Newer Slice")
        self.assertEqual(report["current_focus"], "Plan: Newer Slice")

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
