from __future__ import annotations

import json
import os
import subprocess
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script, temporary_workspace, workspace_fixture


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
        self.assertEqual(report["suggested_workflow"], "plan")
        self.assertIn("verify_repo.py --profile fast", report["recommended_action"])
        self.assertTrue(any("No active plan" in warning for warning in report["warnings"]))

    def test_next_detects_git_changes_and_recommends_verification(self) -> None:
        with temporary_workspace() as workspace:
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
        with temporary_workspace("repo-root") as repo_root:
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
        with temporary_workspace() as workspace:
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

    def test_next_prefers_packet_resume_and_browser_qa_when_execution_packet_requires_it(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            _write_json(
                workspace / ".forge-artifacts" / "workflow-state" / "checkout" / "latest.json",
                {
                    "project": "checkout",
                    "profile": "solo-internal",
                    "intent": "BUILD",
                    "current_stage": "build",
                    "required_stage_chain": ["plan", "build", "test", "quality-gate"],
                    "latest_execution": {
                        "kind": "execution-progress",
                        "label": "Checkout flow polish",
                        "packet_id": "packet-checkout-ui",
                        "status": "active",
                        "current_stage": "build",
                        "completion_state": "in-progress",
                        "next_steps": ["Run browser walkthrough for checkout flow"],
                        "blockers": [],
                        "residual_risk": ["Keyboard path not rechecked yet"],
                        "browser_qa_classification": "required-for-this-packet",
                        "browser_qa_scope": ["checkout flow"],
                        "browser_qa_status": "pending"
                    },
                    "summary": {
                        "status": "active",
                        "primary_kind": "execution-progress",
                        "current_focus": "Build packet: Checkout flow polish [packet-checkout-ui]",
                        "current_stage": "build",
                        "suggested_workflow": "build",
                        "recommended_action": "Resume packet 'packet-checkout-ui' and clear the pending browser QA proof before starting a new slice.",
                        "alternatives": [
                            "After browser QA, continue into 'test'.",
                            "Keep the residual risk visible: Keyboard path not rechecked yet."
                        ],
                        "active_packets": ["packet-checkout-ui"],
                        "browser_qa_pending": ["packet-checkout-ui"]
                    }
                },
            )
            (workspace / "README.md").write_text("# Checkout\n", encoding="utf-8")

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
        self.assertEqual(report["current_focus"], "Build packet: Checkout flow polish [packet-checkout-ui]")
        self.assertIn("pending browser QA proof", report["recommended_action"])
        self.assertEqual(report["signals"]["workflow_summary"]["browser_qa_pending"], ["packet-checkout-ui"])

    def test_next_flags_failed_run_report_as_blocked_debug_work(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            _write_json(
                workspace / ".forge-artifacts" / "workflow-state" / "checkout" / "latest.json",
                {
                    "project": "checkout",
                    "current_stage": "build",
                    "last_recorded_kind": "run-report",
                    "latest_run": {
                        "kind": "run-report",
                        "label": "browser qa evidence capture",
                        "state": "failed",
                        "command_kind": "browser-qa",
                        "recommended_action": "Reproduce the failing browser QA step before continuing.",
                        "warnings": ["Latest browser evidence capture failed."]
                    }
                },
            )
            (workspace / "README.md").write_text("# Checkout\n", encoding="utf-8")

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
        self.assertIn("Reproduce the failing browser QA step", report["recommended_action"])
        self.assertIn("Latest browser evidence capture failed.", " ".join(report["alternatives"]))


if __name__ == "__main__":
    unittest.main()
