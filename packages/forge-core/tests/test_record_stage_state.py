from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class RecordStageStateTests(unittest.TestCase):
    def test_record_stage_state_rejects_stale_expected_previous_stage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")

            seeded = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "plan",
                "--stage-status",
                "active",
                "--required-stage",
                "plan",
                "--required-stage",
                "build",
                "--activation-reason",
                "Initial seed.",
                "--summary",
                "Bootstrap planning stage",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(seeded.returncode, 0, seeded.stderr)

            stale = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "build",
                "--stage-status",
                "active",
                "--required-stage",
                "plan",
                "--required-stage",
                "build",
                "--activation-reason",
                "Start build.",
                "--summary",
                "Build stage",
                "--expected-previous-stage",
                "architect",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )

        self.assertNotEqual(stale.returncode, 0)
        payload = json.loads(stale.stdout)
        self.assertIn("expected_previous_stage", payload["error"])

    def test_build_blocked_transition_can_route_back_to_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")

            seeded = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "plan",
                "--stage-status",
                "active",
                "--required-stage",
                "plan",
                "--required-stage",
                "build",
                "--activation-reason",
                "Start planning.",
                "--summary",
                "Plan the checkout hardening slice",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(seeded.returncode, 0, seeded.stderr)

            revise = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "build",
                "--stage-status",
                "blocked",
                "--required-stage",
                "plan",
                "--required-stage",
                "build",
                "--activation-reason",
                "Build packet blocked.",
                "--decision",
                "revise",
                "--next-stage-override",
                "plan",
                "--expected-previous-stage",
                "plan",
                "--summary",
                "Build packet requested revisions",
                "--next-action",
                "Revise the plan packet before continuing build work.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(revise.returncode, 0, revise.stderr)
            state_path = workspace / ".forge-artifacts" / "workflow-state" / "workflow-workspace" / "latest.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["current_stage"], "plan")
        self.assertEqual(state["last_transition"]["stage_name"], "build")
        self.assertEqual(state["last_transition"]["stage_status"], "blocked")
        self.assertEqual(state["last_transition"]["decision"], "revise")
        self.assertEqual(state["last_transition"]["next_stage_override"], "plan")
        self.assertEqual(state["stages"]["build"]["status"], "blocked")
        self.assertEqual(state["summary"]["status"], "blocked")
        self.assertEqual(state["summary"]["current_focus"], "Blocked workflow stage: build")
        self.assertEqual(state["summary"]["suggested_workflow"], "plan")
        self.assertIn("Revise the plan packet", state["summary"]["recommended_action"])

    def test_deploy_failure_records_release_fields_and_quality_gate_override(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")

            seeded = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "quality-gate",
                "--stage-status",
                "active",
                "--required-stage",
                "self-review",
                "--required-stage",
                "secure",
                "--required-stage",
                "quality-gate",
                "--required-stage",
                "deploy",
                "--activation-reason",
                "Gate approved.",
                "--summary",
                "Gate ready for deploy",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(seeded.returncode, 0, seeded.stderr)

            failed = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "deploy",
                "--stage-status",
                "blocked",
                "--required-stage",
                "self-review",
                "--required-stage",
                "secure",
                "--required-stage",
                "quality-gate",
                "--required-stage",
                "deploy",
                "--activation-reason",
                "Deploy started.",
                "--target",
                "production",
                "--release-artifact-id",
                "rel-42",
                "--rollback-path",
                "rollbacks/rel-42.md",
                "--next-stage-override",
                "quality-gate",
                "--expected-previous-stage",
                "quality-gate",
                "--summary",
                "Deploy failed on production rollout",
                "--next-action",
                "Roll back the failed release and reopen the quality gate.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(failed.returncode, 0, failed.stderr)
            state_path = workspace / ".forge-artifacts" / "workflow-state" / "workflow-workspace" / "latest.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["current_stage"], "quality-gate")
        self.assertEqual(state["last_transition"]["stage_name"], "deploy")
        self.assertEqual(state["last_transition"]["target"], "production")
        self.assertEqual(state["last_transition"]["release_artifact_id"], "rel-42")
        self.assertEqual(state["last_transition"]["rollback_path"], "rollbacks/rel-42.md")
        self.assertEqual(state["summary"]["status"], "blocked")
        self.assertEqual(state["summary"]["current_focus"], "Blocked workflow stage: deploy")
        self.assertEqual(state["summary"]["suggested_workflow"], "quality-gate")


if __name__ == "__main__":
    unittest.main()
