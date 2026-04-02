from __future__ import annotations

import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from support import ROOT_DIR, run_python_script

import common  # noqa: E402
import route_preview  # noqa: E402
import workflow_state_support  # noqa: E402
import track_chain_status  # noqa: E402
import track_execution_progress  # noqa: E402
import track_ui_progress  # noqa: E402


class ToolRoundTripTests(unittest.TestCase):
    def _required_stage_args(self, required_stage_chain: list[str]) -> list[str]:
        args: list[str] = []
        for stage in required_stage_chain:
            args.extend(["--required-stage", stage])
        return args

    def _workflow_state_path(self, workspace: Path, project_name: str) -> Path:
        return workspace / ".forge-artifacts" / "workflow-state" / common.slugify(project_name) / "latest.json"

    def _mark_stage_statuses(self, workflow_state_path: Path, updates: dict[str, str]) -> dict:
        state = json.loads(workflow_state_path.read_text(encoding="utf-8"))
        stages = state.setdefault("stages", {})
        for stage_name, status in updates.items():
            payload = stages.setdefault(stage_name, {})
            payload["status"] = status
        workflow_state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return state

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
                    active_packet=["packet-checkout-api"],
                    blocked_packet=[],
                    review_ready_packet=[],
                    merge_ready_packet=[],
                    next_merge_point="merge-api-and-ui",
                    browser_qa_pending=[],
                    write_scope_overlap=[],
                    sequential_reason=[],
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
                    packet_id="packet-reconciliation",
                    parent_packet="packet-checkout",
                    goal="Stabilize offline reconciliation before merge",
                    source=["docs/specs/reconciliation.md"],
                    scope_path=["src/reconciliation.ts"],
                    owned_scope=["src/reconciliation.ts"],
                    verify_again=["python -m pytest tests/test_reconciliation.py -q"],
                    browser_qa_classification="not-needed",
                    browser_qa_scope=[],
                    browser_qa_status="not-needed",
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
            self.assertEqual(state["latest_chain"]["active_packets"], ["packet-checkout-api"])
            self.assertEqual(state["latest_chain"]["next_merge_point"], "merge-api-and-ui")
            self.assertEqual(state["latest_execution"]["packet_id"], "packet-reconciliation")
            self.assertEqual(state["latest_execution"]["parent_packet"], "packet-checkout")
            self.assertEqual(state["latest_execution"]["goal"], "Stabilize offline reconciliation before merge")
            self.assertEqual(state["latest_execution"]["source_of_truth"], ["docs/specs/reconciliation.md"])
            self.assertEqual(state["latest_execution"]["exact_files_or_paths_in_scope"], ["src/reconciliation.ts"])
            self.assertEqual(state["latest_execution"]["owned_files_or_write_scope"], ["src/reconciliation.ts"])
            self.assertEqual(state["latest_execution"]["verification_to_rerun"], ["python -m pytest tests/test_reconciliation.py -q"])
            self.assertEqual(state["latest_execution"]["browser_qa_classification"], "not-needed")
            self.assertEqual(state["summary"]["current_focus"], "Build packet: Offline reconciliation [packet-reconciliation]")
            self.assertEqual(state["summary"]["suggested_workflow"], "build")
            self.assertEqual(state["summary"]["active_packets"], ["packet-reconciliation"])

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

    def test_ready_for_merge_execution_progress_updates_review_ready_summary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            execution_report = track_execution_progress.build_report(
                Namespace(
                    task="Offline reconciliation",
                    mode="checkpoint-batch",
                    stage="integration",
                    status="completed",
                    completion_state="ready-for-merge",
                    project_name="Example Project",
                    lane="implementer",
                    model_tier="capable",
                    packet_id="packet-reconciliation",
                    parent_packet="packet-checkout",
                    goal="Stabilize offline reconciliation before merge",
                    source=["docs/specs/reconciliation.md"],
                    scope_path=["src/reconciliation.ts"],
                    owned_scope=["src/reconciliation.ts"],
                    verify_again=["python -m pytest tests/test_reconciliation.py -q"],
                    browser_qa_classification="optional-accelerator",
                    browser_qa_scope=["checkout retry flow"],
                    browser_qa_status="pending",
                    proof=["failing reconciliation reproduction"],
                    done=["Added reconciliation service skeleton"],
                    next_step=["Run merge readiness smoke"],
                    blocker=[],
                    risk=["End-to-end verification still pending"],
                )
            )
            execution_json_path, _ = track_execution_progress.persist_report(execution_report, str(workspace))

            workflow_state_path = (
                workspace
                / ".forge-artifacts"
                / "workflow-state"
                / common.slugify("Example Project")
                / "latest.json"
            )
            state = json.loads(workflow_state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["latest_execution"]["source_path"], str(execution_json_path))
        self.assertEqual(state["latest_execution"]["completion_state"], "ready-for-merge")
        self.assertEqual(state["latest_execution"]["next_steps"], ["Run merge readiness smoke"])
        self.assertEqual(state["latest_execution"]["residual_risk"], ["End-to-end verification still pending"])
        self.assertEqual(state["latest_execution"]["browser_qa_classification"], "optional-accelerator")
        self.assertEqual(state["latest_execution"]["browser_qa_status"], "pending")
        self.assertEqual(state["latest_execution"]["browser_qa_scope"], ["checkout retry flow"])
        self.assertEqual(execution_report["lane"], "implementer")
        self.assertEqual(execution_report["model_tier"], "capable")
        self.assertEqual(state["summary"]["status"], "review-ready")
        self.assertEqual(state["summary"]["suggested_workflow"], "review")
        self.assertEqual(state["summary"]["current_focus"], "Review ready: Offline reconciliation [packet-reconciliation]")
        self.assertEqual(state["summary"]["browser_qa_pending"], ["packet-reconciliation"])

    def test_solo_profile_recorders_update_workflow_state_spine(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            required_stage_chain = [
                "brainstorm",
                "plan",
                "spec-review",
                "build",
                "test",
                "quality-gate",
                "release-readiness",
                "adoption-check",
            ]
            required_stage_args = self._required_stage_args(required_stage_chain)

            direction = run_python_script(
                "record_direction_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--profile",
                "solo-internal",
                "--intent",
                "new feature direction",
                *required_stage_args,
                "--stage-status",
                "completed",
                "--mode",
                "discovery-lite",
                "--decision-state",
                "direction-locked",
                "--activation-reason",
                "Greenfield feature needs an explicit direction brief.",
                "--summary",
                "Direction locked for the checkout flow.",
                "--note",
                "Discovery-lite confirms the path before implementation.",
                "--next-action",
                "Move into plan with the locked direction.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(direction.returncode, 0, direction.stderr)
            direction_report = json.loads(direction.stdout)

            spec_review = run_python_script(
                "record_spec_review_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--profile",
                "solo-internal",
                "--intent",
                "new feature direction",
                *required_stage_args,
                "--stage-status",
                "completed",
                "--decision",
                "go",
                "--activation-reason",
                "Boundary risk was reviewed before build.",
                "--summary",
                "Spec review cleared the implementation packet.",
                "--review-iteration",
                "1",
                "--max-review-iterations",
                "3",
                "--note",
                "Packet is clear enough for build.",
                "--next-action",
                "Start implementation with the reviewed spec.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(spec_review.returncode, 0, spec_review.stderr)
            spec_review_report = json.loads(spec_review.stdout)

            adoption_check = run_python_script(
                "record_adoption_check.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--profile",
                "solo-internal",
                "--intent",
                "new feature direction",
                *required_stage_args,
                "--stage-status",
                "completed",
                "--activation-reason",
                "Shared-env release needs a final adoption pass.",
                "--target",
                "shared env release",
                "--summary",
                "Adoption check confirms the release was taken up.",
                "--signal",
                "Users completed the new flow without follow-up issues.",
                "--release-action",
                "monitor",
                "--next-action",
                "Monitor the release after rollout.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(adoption_check.returncode, 0, adoption_check.stderr)
            adoption_check_report = json.loads(adoption_check.stdout)

            workflow_state_path = (
                workspace
                / ".forge-artifacts"
                / "workflow-state"
                / common.slugify("Example Project")
                / "latest.json"
            )
            self.assertTrue(workflow_state_path.exists())
            state = json.loads(workflow_state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["profile"], "solo-internal")
        self.assertEqual(state["intent"], "new feature direction")
        self.assertEqual(state["required_stage_chain"], required_stage_chain)
        self.assertEqual(state["current_stage"], "adoption-check")

        self.assertEqual(state["latest_direction"]["current_stage"], "brainstorm")
        self.assertEqual(state["latest_spec_review"]["current_stage"], "spec-review")
        self.assertEqual(state["latest_adoption_check"]["current_stage"], "adoption-check")
        self.assertEqual(state["latest_adoption_check"]["release_actions"], ["monitor"])
        self.assertEqual(state["latest_adoption_check"]["friction_categories"], [])

        self.assertEqual(state["latest_direction"]["source_path"], direction_report["artifacts"]["json"])
        self.assertEqual(state["latest_spec_review"]["source_path"], spec_review_report["artifacts"]["json"])
        self.assertEqual(state["latest_adoption_check"]["source_path"], adoption_check_report["artifacts"]["json"])

        self.assertEqual(state["stages"]["brainstorm"]["status"], "completed")
        self.assertEqual(state["stages"]["plan"]["status"], "required")
        self.assertEqual(state["stages"]["spec-review"]["status"], "completed")
        self.assertEqual(state["stages"]["build"]["status"], "required")
        self.assertEqual(state["stages"]["test"]["status"], "required")
        self.assertEqual(state["stages"]["quality-gate"]["status"], "required")
        self.assertEqual(state["stages"]["adoption-check"]["status"], "completed")
        self.assertEqual(state["stages"]["brainstorm"]["source_path"], direction_report["artifacts"]["json"])
        self.assertEqual(state["stages"]["spec-review"]["source_path"], spec_review_report["artifacts"]["json"])
        self.assertEqual(state["stages"]["adoption-check"]["source_path"], adoption_check_report["artifacts"]["json"])

    def test_solo_public_release_chain_uses_recorded_workflow_state_for_release_gates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_name = "Public Launch"
            required_stage_chain = [
                "brainstorm",
                "plan",
                "spec-review",
                "build",
                "test",
                "review-pack",
                "self-review",
                "secure",
                "quality-gate",
                "release-doc-sync",
                "release-readiness",
                "deploy",
                "adoption-check",
            ]
            required_stage_args = self._required_stage_args(required_stage_chain)

            (workspace / "app").mkdir(parents=True, exist_ok=True)
            (workspace / "app" / "page.tsx").write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (workspace / ".env.example").write_text("APP_NAME=launch\n", encoding="utf-8")

            direction = run_python_script(
                "record_direction_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                project_name,
                "--profile",
                "solo-public",
                "--intent",
                "public launch",
                *required_stage_args,
                "--stage-status",
                "completed",
                "--mode",
                "discovery-full",
                "--decision-state",
                "direction-locked",
                "--activation-reason",
                "Public launch needs an explicit direction brief.",
                "--summary",
                "Direction locked for the public launch slice.",
                "--note",
                "Boundary and rollout expectations are explicit.",
                "--next-action",
                "Move into spec-review.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(direction.returncode, 0, direction.stderr)

            spec_review = run_python_script(
                "record_spec_review_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                project_name,
                "--profile",
                "solo-public",
                "--intent",
                "public launch",
                *required_stage_args,
                "--stage-status",
                "completed",
                "--decision",
                "go",
                "--activation-reason",
                "Public boundary risk was reviewed before build.",
                "--summary",
                "Spec review cleared the public launch packet.",
                "--review-iteration",
                "1",
                "--max-review-iterations",
                "3",
                "--note",
                "Packet is ready for implementation.",
                "--next-action",
                "Start implementation.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(spec_review.returncode, 0, spec_review.stderr)

            execution = run_python_script(
                "track_execution_progress.py",
                "Public launch implementation",
                "--mode",
                "checkpoint-batch",
                "--stage",
                "implementation",
                "--status",
                "completed",
                "--completion-state",
                "ready-for-merge",
                "--profile",
                "solo-public",
                "--intent",
                "public launch",
                *required_stage_args,
                "--project-name",
                project_name,
                "--harness-available",
                "no",
                "--proof",
                "Public launch smoke pack passed.",
                "--done",
                "Implemented the release slice.",
                "--next",
                "Run release gate checks.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
                cwd=workspace,
            )
            self.assertEqual(execution.returncode, 0, execution.stderr)

            review = run_python_script(
                "record_review_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                project_name,
                "--scope",
                "public-launch",
                "--review-kind",
                "release-review",
                "--disposition",
                "ready-for-merge",
                "--branch-state",
                "clean branch",
                "--evidence",
                "Public launch smoke pack passed.",
                "--no-finding-rationale",
                "No material release findings remain.",
                "--next-action",
                "Run final gate checks.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(review.returncode, 0, review.stderr)

            workflow_state_path = self._workflow_state_path(workspace, project_name)
            state = self._mark_stage_statuses(
                workflow_state_path,
                {
                    "plan": "completed",
                    "build": "completed",
                    "test": "completed",
                    "review-pack": "completed",
                    "self-review": "completed",
                    "secure": "completed",
                    "quality-gate": "required",
                    "release-doc-sync": "required",
                    "release-readiness": "required",
                    "deploy": "required",
                    "adoption-check": "required",
                },
            )
            self.assertEqual(state["profile"], "solo-public")
            self.assertEqual(state["stages"]["review-pack"]["status"], "completed")
            self.assertEqual(state["stages"]["release-doc-sync"]["status"], "required")

            review_pack = run_python_script(
                "review_pack.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
                "--persist",
                "--output-dir",
                str(workspace),
            )
            self.assertEqual(review_pack.returncode, 0, review_pack.stderr)
            review_pack_report = json.loads(review_pack.stdout)
            self.assertEqual(review_pack_report["status"], "PASS")
            self.assertEqual(review_pack_report["operating_profile"], "solo-public")
            self.assertTrue(review_pack_report["public_surface"])

            release_doc_sync = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "docs/release/public-readiness.md",
                "--format",
                "json",
                "--persist",
                "--output-dir",
                str(workspace),
            )
            self.assertEqual(release_doc_sync.returncode, 0, release_doc_sync.stderr)
            docs_report = json.loads(release_doc_sync.stdout)
            self.assertEqual(docs_report["status"], "PASS")

            gate = run_python_script(
                "record_quality_gate.py",
                "--workspace",
                str(workspace),
                "--project-name",
                project_name,
                "--profile",
                "standard",
                "--target-claim",
                "deploy",
                "--decision",
                "go",
                "--evidence",
                "Public launch smoke pack passed.",
                "--response",
                "I verified: public launch smoke pack passed. Correct because release checks stayed green. Fixed: yes.",
                "--why",
                "Public launch is ready for rollout gating.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)
            gate_report = json.loads(gate.stdout)
            self.assertEqual(gate_report["status"], "PASS")
            self.assertEqual(gate_report["operating_profile"], "solo-public")

            readiness = run_python_script(
                "release_readiness.py",
                "--workspace",
                str(workspace),
                "--profile",
                "standard",
                "--format",
                "json",
                "--persist",
                "--output-dir",
                str(workspace),
            )
            self.assertEqual(readiness.returncode, 1, readiness.stderr)
            readiness_report = json.loads(readiness.stdout)

        self.assertEqual(readiness_report["effective_profile"], "solo-public")

    def test_route_preview_persist_seeds_workflow_state_for_run_guidance(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            report = route_preview.build_report(
                Namespace(
                    prompt="Deploy the app to external users with a public launch",
                    repo_signal=[],
                    workspace_router=None,
                    changed_files=None,
                    has_harness="auto",
                    format="json",
                    persist=False,
                    output_dir=None,
                )
            )
            route_preview.persist_report(report, str(workspace))

            workflow_state_path = self._workflow_state_path(workspace, "workspace")
            state = json.loads(workflow_state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["latest_route_preview"]["current_stage"], "review-pack")
            self.assertEqual(state["summary"]["primary_kind"], "route-preview")
            self.assertEqual(state["summary"]["suggested_workflow"], "review-pack")

            run_result = run_python_script(
                "run_with_guidance.py",
                "--workspace",
                str(workspace),
                "--timeout-ms",
                "2000",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
                "--",
                "python",
                "-c",
                "print('ready')",
                cwd=workspace,
            )
            self.assertEqual(run_result.returncode, 0, run_result.stderr)
            run_report = json.loads(run_result.stdout)
            state = json.loads(workflow_state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["profile"], "solo-public")
        self.assertEqual(state["intent"], "DEPLOY")
        self.assertEqual(
            state["required_stage_chain"],
            ["review-pack", "self-review", "secure", "quality-gate", "release-doc-sync", "release-readiness", "deploy", "adoption-check"],
        )
        self.assertEqual(state["current_stage"], "review-pack")
        self.assertEqual(state["latest_route_preview"]["current_stage"], "review-pack")
        self.assertEqual(state["stages"]["review-pack"]["status"], "required")
        self.assertEqual(state["stages"]["release-readiness"]["status"], "required")
        self.assertEqual(state["latest_run"]["current_stage"], "review-pack")
        self.assertEqual(state["latest_run"]["required_stage_chain"], state["required_stage_chain"])
        self.assertEqual(run_report["current_stage"], "review-pack")
        self.assertEqual(run_report["required_stage_chain"], state["required_stage_chain"])


if __name__ == "__main__":
    unittest.main()
