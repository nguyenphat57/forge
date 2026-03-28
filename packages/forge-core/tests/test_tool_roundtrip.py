from __future__ import annotations

import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from support import ROOT_DIR, run_python_script

import common  # noqa: E402
import workflow_state_support  # noqa: E402
import track_chain_status  # noqa: E402
import track_execution_progress  # noqa: E402
import track_ui_progress  # noqa: E402


class ToolRoundTripTests(unittest.TestCase):
    def test_backend_brief_round_trip_passes_checker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            generate = run_python_script(
                "generate_backend_brief.py",
                "Add bulk order cancellation endpoint",
                "--pattern",
                "sync-api",
                "--runtime",
                "python-service",
                "--surface",
                "cancel-orders",
                "--persist",
                "--project-name",
                "Example Project",
                "--output-dir",
                str(output_dir),
                "--format",
                "json",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            artifact_dir = output_dir / ".forge-artifacts" / "backend-briefs" / common.slugify("Example Project")
            self.assertTrue((artifact_dir / "MASTER.md").exists())

            check = run_python_script(
                "check_backend_brief.py",
                str(artifact_dir),
                "--surface",
                "cancel-orders",
                "--format",
                "json",
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "PASS")

    def test_ui_brief_round_trip_passes_checker_for_frontend_and_visualize(self) -> None:
        modes = [
            ("frontend", "Refresh checkout for tablet POS", "react-vite", "checkout"),
            ("visualize", "Explore calmer kitchen dashboard direction", "mobile-webview", "kitchen-dashboard"),
        ]
        for mode, summary, stack, screen in modes:
            with self.subTest(mode=mode):
                with TemporaryDirectory() as temp_dir:
                    output_dir = Path(temp_dir)
                    generate = run_python_script(
                        "generate_ui_brief.py",
                        summary,
                        "--mode",
                        mode,
                        "--stack",
                        stack,
                        "--platform",
                        "tablet",
                        "--screen",
                        screen,
                        "--persist",
                        "--project-name",
                        "Example Project",
                        "--output-dir",
                        str(output_dir),
                        "--format",
                        "json",
                    )
                    self.assertEqual(generate.returncode, 0, generate.stderr)

                    artifact_dir = output_dir / ".forge-artifacts" / "ui-briefs" / common.slugify("Example Project") / mode
                    self.assertTrue((artifact_dir / "MASTER.md").exists())

                    check = run_python_script(
                        "check_ui_brief.py",
                        str(artifact_dir),
                        "--mode",
                        mode,
                        "--screen",
                        screen,
                        "--format",
                        "json",
                    )
                    self.assertEqual(check.returncode, 0, check.stderr)
                    report = json.loads(check.stdout)
                    self.assertEqual(report["status"], "PASS")

    def test_capture_continuity_writes_scoped_entry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            brain_dir = Path(temp_dir) / ".brain"
            result = run_python_script(
                "capture_continuity.py",
                "Compatibility window must stay one release",
                "--kind",
                "decision",
                "--scope",
                "orders-api",
                "--evidence",
                "docs/DESIGN.md",
                "--brain-dir",
                str(brain_dir),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            entries = json.loads((brain_dir / "decisions.json").read_text(encoding="utf-8"))

        self.assertEqual(report["entry"]["scope"], "orders-api")
        self.assertEqual(entries[0]["summary"], "Compatibility window must stay one release")

    def test_execution_progress_requires_proof_for_ready_states(self) -> None:
        with self.assertRaises(ValueError):
            track_execution_progress.build_report(
                Namespace(
                    task="Offline reconciliation",
                    mode="checkpoint-batch",
                    stage="integration",
                    status="completed",
                    completion_state="ready-for-review",
                    project_name="workspace",
                    lane="implementer",
                    model_tier="capable",
                    proof=[],
                    done=[],
                    next_step=[],
                    blocker=[],
                    risk=[],
                )
            )

    def test_chain_status_rejects_overflowing_review_iteration(self) -> None:
        with self.assertRaises(ValueError):
            track_chain_status.build_report(
                Namespace(
                    chain="Checkout rewrite",
                    project_name="workspace",
                    status="active",
                    current_stage="spec-review",
                    completed_stage=[],
                    next_stage=[],
                    active_skill=[],
                    active_lane=[],
                    lane_model=[],
                    blocker=[],
                    risk=[],
                    gate_decision=None,
                    review_iteration=4,
                    max_review_iterations=3,
                )
            )

    def test_ui_progress_persists_remaining_stages(self) -> None:
        with TemporaryDirectory() as temp_dir:
            payload = track_ui_progress.build_payload(
                Namespace(
                    project_name="workspace",
                    mode="frontend",
                    task="Checkout tablet refresh",
                    stage="implementation",
                    status="active",
                    note=["Waiting on responsive review"],
                )
            )
            json_path, md_path = track_ui_progress.persist_payload(payload, temp_dir)

            persisted = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = md_path.read_text(encoding="utf-8")

        self.assertEqual(persisted["remaining_stages"], ["responsive-a11y-review", "handover"])
        self.assertIn("Waiting on responsive review", markdown)

    def test_progress_trackers_update_unified_workflow_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            chain_report = track_chain_status.build_report(
                Namespace(
                    chain="Checkout rewrite",
                    project_name="Example Project",
                    status="active",
                    current_stage="implementation",
                    completed_stage=["plan"],
                    next_stage=["quality-gate"],
                    active_skill=["build"],
                    active_lane=["implementer"],
                    lane_model=["implementer=capable"],
                    blocker=[],
                    risk=["Merge verification still pending"],
                    gate_decision=None,
                    review_iteration=1,
                    max_review_iterations=3,
                )
            )
            chain_json_path, _ = track_chain_status.persist_report(chain_report, str(workspace))

            execution_report = track_execution_progress.build_report(
                Namespace(
                    task="Offline reconciliation",
                    mode="checkpoint-batch",
                    stage="integration",
                    status="active",
                    completion_state="in-progress",
                    project_name="Example Project",
                    lane="implementer",
                    model_tier="capable",
                    proof=["failing reconciliation reproduction"],
                    done=["Added reconciliation service skeleton"],
                    next_step=["Wire retry policy into sync manager"],
                    blocker=[],
                    risk=["End-to-end verification still pending"],
                )
            )
            execution_json_path, _ = track_execution_progress.persist_report(execution_report, str(workspace))

            ui_payload = track_ui_progress.build_payload(
                Namespace(
                    project_name="Example Project",
                    mode="frontend",
                    task="Checkout tablet refresh",
                    stage="responsive-a11y-review",
                    status="active",
                    note=["Keyboard navigation review pending"],
                )
            )
            ui_json_path, _ = track_ui_progress.persist_payload(ui_payload, str(workspace))

            workflow_state_path = (
                workspace
                / ".forge-artifacts"
                / "workflow-state"
                / common.slugify("Example Project")
                / "latest.json"
            )
            self.assertTrue(workflow_state_path.exists())
            state = json.loads(workflow_state_path.read_text(encoding="utf-8"))

            self.assertEqual(state["latest_chain"]["source_path"], str(chain_json_path))
            self.assertEqual(state["latest_execution"]["source_path"], str(execution_json_path))
            self.assertEqual(state["latest_ui"]["source_path"], str(ui_json_path))
            self.assertEqual(state["summary"]["primary_kind"], "execution-progress")
            self.assertEqual(state["summary"]["current_focus"], "Execution task: Offline reconciliation")

            run_report = {
                "status": "PASS",
                "recorded_at": "2026-03-28T10:00:00+00:00",
                "project": "Example Project",
                "command_display": "python build_fixture.py",
                "command_kind": "build",
                "state": "completed",
                "suggested_workflow": "test",
                "recommended_action": "Build passed. Run the nearest targeted test or smoke check before claiming the slice is done.",
                "warnings": [],
            }
            run_json_path = workspace / ".forge-artifacts" / "run-reports" / "build.json"
            run_json_path.parent.mkdir(parents=True, exist_ok=True)
            run_json_path.write_text(json.dumps(run_report, indent=2, ensure_ascii=False), encoding="utf-8")
            workflow_state_support.record_workflow_event("run-report", run_report, output_dir=str(workspace), source_path=run_json_path)

            gate_report = {
                "status": "WARN",
                "recorded_at": "2026-03-28T10:05:00+00:00",
                "project": "Example Project",
                "profile": "standard",
                "target_claim": "ready-for-merge",
                "decision": "conditional",
                "evidence_read": ["pytest tests/test_checkout.py"],
                "response": "I verified: checkout regression passed. Correct because the retry path now stays stable. Fixed: yes.",
                "why": "Residual merge risk remains until one more smoke pass runs.",
                "next_evidence": ["Run merge-readiness smoke on checkout flow"],
                "risks": ["One manual smoke is still pending"],
            }
            gate_json_path = workspace / ".forge-artifacts" / "quality-gates" / common.slugify("Example Project") / "gate.json"
            gate_json_path.parent.mkdir(parents=True, exist_ok=True)
            gate_json_path.write_text(json.dumps(gate_report, indent=2, ensure_ascii=False), encoding="utf-8")
            workflow_state_support.record_workflow_event("quality-gate", gate_report, output_dir=str(workspace), source_path=gate_json_path)

            state = json.loads(workflow_state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["latest_run"]["source_path"], str(run_json_path))
        self.assertEqual(state["latest_gate"]["source_path"], str(gate_json_path))
        self.assertEqual(state["last_recorded_kind"], "quality-gate")
        self.assertEqual(state["summary"]["primary_kind"], "quality-gate")
        self.assertEqual(state["summary"]["current_focus"], "Conditional gate: ready-for-merge")


if __name__ == "__main__":
    unittest.main()
