from __future__ import annotations

import json
import subprocess
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
            "Resume the highest-signal pending task: Write migration verification notes.",
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


if __name__ == "__main__":
    unittest.main()
