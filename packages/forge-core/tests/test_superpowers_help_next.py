from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class SuperpowersHelpNextTests(unittest.TestCase):
    def test_design_approved_brainstorm_advances_next_to_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")

            direction = run_python_script(
                "record_direction_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--profile",
                "solo-internal",
                "--intent",
                "BUILD",
                "--required-stage",
                "brainstorm",
                "--required-stage",
                "plan",
                "--required-stage",
                "build",
                "--stage-status",
                "completed",
                "--mode",
                "discovery-full",
                "--decision-state",
                "design-approved",
                "--activation-reason",
                "Design doc approved.",
                "--artifact",
                "docs/specs/2026-04-21-checkout-design.md",
                "--summary",
                "Checkout design approved",
                "--next-action",
                "Write the implementation plan.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(direction.returncode, 0, direction.stderr)

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
        self.assertEqual(report["current_focus"], "Recorded workflow stage: plan")
        self.assertEqual(report["suggested_workflow"], "plan")

    def test_plan_stage_stays_active_until_execution_choice_is_recorded(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")

            stage = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "plan",
                "--stage-status",
                "completed",
                "--required-stage",
                "plan",
                "--required-stage",
                "build",
                "--required-stage",
                "test",
                "--activation-reason",
                "Implementation plan written.",
                "--decision",
                "execution-choice-required",
                "--summary",
                "Implementation plan written and waiting for execution choice",
                "--next-action",
                "Choose inline-execution or subagent-driven before build.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(stage.returncode, 0, stage.stderr)

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
        self.assertEqual(report["current_focus"], "Recorded workflow stage: plan")
        self.assertEqual(report["suggested_workflow"], "plan")
        self.assertIn("Choose inline-execution or subagent-driven", report["recommended_action"])


if __name__ == "__main__":
    unittest.main()
