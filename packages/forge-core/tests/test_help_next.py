from __future__ import annotations

import json
import os
import subprocess
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import copied_workspace_fixture, run_python_script, temporary_workspace, workspace_fixture


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

    def test_next_uses_codebase_map_when_repo_is_mapped_but_not_planned(self) -> None:
        with copied_workspace_fixture("map_codebase_next_workspace", target_name="mapped-workspace") as workspace:
            mapped = run_python_script("map_codebase.py", "--workspace", str(workspace), "--format", "json")
            self.assertEqual(mapped.returncode, 0, mapped.stderr)

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

        self.assertEqual(report["current_stage"], "mapped")
        self.assertTrue(str(report["signals"]["codebase_summary"]).endswith("summary.md"))
        self.assertEqual(report["suggested_workflow"], "plan")
        self.assertIn("brownfield codebase map", report["recommended_action"])

    def test_next_prefers_active_change_artifact_when_no_session_exists(self) -> None:
        with temporary_workspace("change-workspace") as workspace:
            (workspace / "README.md").write_text("# Change Workspace\n", encoding="utf-8")
            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Add refund queue",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)

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

        self.assertEqual(report["current_stage"], "change-active")
        self.assertIn("Resume the active change", report["recommended_action"])

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
        self.assertEqual(report["suggested_workflow"], "map-codebase")
        self.assertIn("Run `doctor` and `map-codebase`", report["recommended_action"])
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

    def test_next_is_release_tail_aware_from_workflow_state_and_readiness(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            _write_json(
                workspace / ".forge-artifacts" / "workflow-state" / "checkout" / "latest.json",
                {
                    "project": "checkout",
                    "profile": "solo-public",
                    "intent": "DEPLOY",
                    "current_stage": "adoption-check",
                    "required_stage_chain": [
                        "review-pack",
                        "self-review",
                        "quality-gate",
                        "release-doc-sync",
                        "release-readiness",
                        "deploy",
                        "adoption-check",
                    ],
                    "stages": {
                        "review-pack": {"status": "completed"},
                        "self-review": {"status": "completed"},
                        "quality-gate": {"status": "completed"},
                        "release-doc-sync": {"status": "completed"},
                        "release-readiness": {"status": "completed"},
                        "deploy": {"status": "completed"},
                        "adoption-check": {"status": "required"},
                    },
                    "summary": {
                        "status": "active",
                        "primary_kind": "route-preview",
                        "current_focus": "Recorded workflow stage: adoption-check",
                        "current_stage": "adoption-check",
                        "suggested_workflow": "adoption-check",
                        "recommended_action": "Continue the recorded release tail before opening new scope.",
                        "alternatives": ["Keep the release tail visible."],
                    },
                    "latest_gate": {
                        "decision": "go",
                        "why": "Release gate is green.",
                    },
                },
            )
            _write_json(
                workspace / ".forge-artifacts" / "release-readiness" / "checkout" / "latest.json",
                {
                    "status": "PASS",
                    "release_tier": "public-broad",
                    "summary": "Core release contract looks ready.",
                },
            )
            _write_json(
                workspace / ".forge-artifacts" / "adoption-check" / "checkout" / "latest.json",
                {
                    "recorded_at": "2026-04-01T00:00:00+00:00",
                    "project": "checkout",
                    "summary": "Adoption signal shows a stable launch.",
                    "impact": "supports",
                    "confidence": "high",
                    "target": "public launch",
                    "stage_name": "adoption-check",
                    "stage_status": "completed",
                    "signals": ["Conversion is stable after launch."],
                    "next_actions": ["Keep monitoring the release tail."],
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

        self.assertEqual(report["current_stage"], "change-active")
        self.assertIn("Release tail: adoption-check (public-broad)", report["current_focus"])
        self.assertIn("Release tier: public-broad", report["recommended_action"])
        self.assertEqual(report["signals"]["release_readiness_tier"], "public-broad")
        self.assertIn("supports / high", report["signals"]["latest_adoption_signal"])

if __name__ == "__main__":
    unittest.main()
