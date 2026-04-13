from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import build_route_args, run_python_script

import route_preview  # noqa: E402


class HelpNextWorkflowStateTests(unittest.TestCase):
    def _init_synced_git_repo(self, workspace: Path, remote: Path) -> None:
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "checkout", "-b", "main"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "commit", "-m", "init"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=workspace, check=True, capture_output=True, text=True, encoding="utf-8")

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
        self.assertEqual(report["suggested_workflow"], "review")
        self.assertEqual(report["current_focus"], "Recorded workflow stage: self-review")
        self.assertEqual(
            report["recommended_action"],
            "Resume the recorded workflow stage 'self-review' before opening new scope.",
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
                            "residual_risk": []
                        },
                        "summary": {
                            "status": "active",
                            "primary_kind": "execution-progress",
                            "current_focus": "Build packet: Offline reconciliation [packet-reconciliation]",
                            "current_stage": "integration",
                            "suggested_workflow": "integration",
                            "recommended_action": "Continue the active execution slice.",
                            "alternatives": []
                        }
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

            execution = run_python_script(
                "track_execution_progress.py",
                "Checkout rollback slice",
                "--mode",
                "checkpoint-batch",
                "--stage",
                "integration",
                "--status",
                "completed",
                "--completion-state",
                "ready-for-review",
                "--project-name",
                "workflow-workspace",
                "--harness-available",
                "no",
                "--proof",
                "pytest tests/test_checkout.py",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
                cwd=workspace,
            )
            self.assertEqual(execution.returncode, 0, execution.stderr)

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
        helper = Path(__file__).resolve().parents[0] / "fixtures" / "run_helpers" / "build_fixture.py"
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")

            execution = run_python_script(
                "track_execution_progress.py",
                "Deploy readiness slice",
                "--mode",
                "checkpoint-batch",
                "--stage",
                "release-checks",
                "--status",
                "completed",
                "--completion-state",
                "ready-for-merge",
                "--project-name",
                "Example Project",
                "--harness-available",
                "no",
                "--proof",
                "python scripts/build_release.py --format json",
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
                "Example Project",
                "--scope",
                "deploy-readiness",
                "--review-kind",
                "quality-pass",
                "--disposition",
                "ready-for-merge",
                "--branch-state",
                "clean branch",
                "--evidence",
                "python scripts/build_release.py --format json",
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

            run_result = run_python_script(
                "run_with_guidance.py",
                "--workspace",
                str(workspace),
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
                cwd=workspace,
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

    def test_next_filters_stale_merge_handoff_when_repo_is_clean_and_synced(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            remote = root / "remote.git"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            self._init_synced_git_repo(workspace, remote)

            state_dir = workspace / ".forge-artifacts" / "workflow-state" / "workflow-workspace"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "project": "Workflow Workspace",
                        "current_stage": "quality-gate",
                        "last_recorded_kind": "quality-gate",
                        "last_transition": {
                            "kind": "quality-gate",
                            "stage_name": "quality-gate",
                            "stage_status": "completed",
                            "transition_id": "gate-ready-for-merge",
                            "recorded_at": "2026-04-02T00:00:00+00:00",
                            "source_path": None,
                        },
                        "latest_gate": {
                            "kind": "quality-gate",
                            "project": "Workflow Workspace",
                            "label": "ready-for-merge",
                            "decision": "go",
                            "why": "Fresh verification is already aligned.",
                            "response": "I verified: the slice is ready for handoff.",
                            "next_evidence": [],
                            "evidence_read": ["pytest tests/test_checkout.py"],
                            "risks": [],
                        },
                        "summary": {
                            "status": "active",
                            "primary_kind": "quality-gate",
                            "current_focus": "Gate approved: ready-for-merge",
                            "current_stage": "quality-gate",
                            "suggested_workflow": "review",
                            "recommended_action": "Proceed with the approved handoff for 'ready-for-merge'.",
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

        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["current_focus"], "No active work slice detected from repo state.")
        self.assertIsNone(report["signals"]["workflow_summary"])
        self.assertTrue(
            any("Filtered stale merge-ready workflow-state" in warning for warning in report["warnings"]),
            report["warnings"],
        )

    def test_next_ignores_packet_index_without_canonical_workflow_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_slug = "workflow-workspace"
            state_dir = workspace / ".forge-artifacts" / "workflow-state" / project_slug
            state_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"workflow-workspace"}\n', encoding="utf-8")
            (state_dir / "packet-index.json").write_text(
                json.dumps(
                    {
                        "project": "Workflow Workspace",
                        "updated_at": "2026-04-02T00:00:00+00:00",
                        "current_stage": "build",
                        "current_packet": "packet-checkout-ui",
                        "packet_mode": "fast-lane",
                        "active_packets": ["packet-checkout-ui"],
                        "blocked_packets": [],
                        "review_ready_packets": [],
                        "merge_ready_packets": [],
                        "browser_qa_pending": [],
                        "merge_target": None,
                        "next_merge_point": None,
                        "summary": {
                            "status": "active",
                            "primary_kind": "execution-progress",
                            "current_focus": "Fast-lane packet: Checkout copy polish [packet-checkout-ui]",
                            "recommended_action": "Continue fast-lane packet 'packet-checkout-ui' with explicit proof rerun.",
                            "suggested_workflow": "build"
                        }
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
        self.assertEqual(report["status"], "WARN")
        self.assertIsNone(report["signals"]["workflow_state_source"])
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["current_focus"], "No active work slice detected from repo state.")
        self.assertIn("bootstrap_workflow_state.py", report["recommended_action"])

    def test_next_treats_legacy_artifacts_and_docs_as_sidecars_until_bootstrapped(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "docs" / "plans").mkdir(parents=True, exist_ok=True)
            (workspace / "docs" / "plans" / "checkout.md").write_text("# Plan: Checkout hardening\n", encoding="utf-8")
            (workspace / ".brain").mkdir(parents=True, exist_ok=True)
            (workspace / ".brain" / "session.json").write_text(
                json.dumps(
                    {
                        "working_on": {"task": "Finish checkout hardening", "status": "active", "files": []},
                        "pending_tasks": ["Run checkout smoke"],
                        "verification": [],
                        "decisions_made": [],
                        "risks": [],
                        "blockers": [],
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            legacy_execution_dir = workspace / ".forge-artifacts" / "execution-progress" / "workflow-workspace"
            legacy_execution_dir.mkdir(parents=True, exist_ok=True)
            (legacy_execution_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "recorded_at": "2026-04-02T00:00:00+00:00",
                        "project": "Workflow Workspace",
                        "task": "Checkout hardening",
                        "status": "active",
                        "current_stage": "integration",
                        "completion_state": "in-progress",
                        "proof": ["pytest tests/test_checkout.py"],
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
        self.assertEqual(report["status"], "WARN")
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertIsNone(report["signals"]["workflow_state_source"])
        self.assertEqual(report["signals"]["latest_plan_title"], "Checkout hardening")
        self.assertIn("bootstrap_workflow_state.py", report["recommended_action"])

    def test_next_can_resume_after_bootstrap_seeds_canonical_workflow_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "docs" / "plans").mkdir(parents=True, exist_ok=True)
            (workspace / "docs" / "plans" / "checkout.md").write_text(
                "# Plan: Checkout hardening\n\n- Validate retry path.\n",
                encoding="utf-8",
            )

            bootstrap = run_python_script(
                "bootstrap_workflow_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--format",
                "json",
            )
            self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
            bootstrap_report = json.loads(bootstrap.stdout)
            self.assertEqual(bootstrap_report["status"], "PASS")
            self.assertEqual(bootstrap_report["bootstrap_source"], "plan")

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
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")
        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["current_focus"], "Recorded workflow stage: plan")
        self.assertEqual(report["suggested_workflow"], "plan")

    def test_next_handles_empty_canonical_root_without_activating_work(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            state_dir = workspace / ".forge-artifacts" / "workflow-state" / "workflow-workspace"
            state_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (state_dir / "latest.json").write_text("{}", encoding="utf-8")

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
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")
        self.assertEqual(report["current_focus"], "No active work slice detected from repo state.")

    def test_next_ignores_corrupt_canonical_root_and_packet_index(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            state_dir = workspace / ".forge-artifacts" / "workflow-state" / "workflow-workspace"
            state_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (state_dir / "latest.json").write_text("{not-json", encoding="utf-8")
            (state_dir / "packet-index.json").write_text(
                json.dumps({"project": "Workflow Workspace", "current_stage": "build"}, indent=2, ensure_ascii=False),
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
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertIsNone(report["signals"]["workflow_state_source"])
        self.assertTrue(any("Invalid JSON in workflow state" in warning for warning in report["warnings"]), report["warnings"])
        self.assertTrue(any("packet-index" in warning for warning in report["warnings"]), report["warnings"])

    def test_next_uses_blocked_secure_stage_recorded_via_stage_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")

            secure = run_python_script(
                "record_stage_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--stage-name",
                "secure",
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
                "Security review started.",
                "--summary",
                "Secure stage blocked on release finding",
                "--next-action",
                "Fix the release hardening finding before reopening the gate.",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(secure.returncode, 0, secure.stderr)

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
        self.assertEqual(report["suggested_workflow"], "secure")
        self.assertEqual(report["current_focus"], "Blocked workflow stage: secure")
        self.assertIn("Fix the release hardening finding", report["recommended_action"])

    def test_next_bootstrap_can_seed_from_spec_sidecar(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (workspace / "docs" / "specs").mkdir(parents=True, exist_ok=True)
            (workspace / "docs" / "specs" / "checkout.md").write_text(
                "# Spec: Checkout architecture hardening\n\n- Narrow the release boundary.\n",
                encoding="utf-8",
            )

            bootstrap = run_python_script(
                "bootstrap_workflow_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--format",
                "json",
            )
            self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
            bootstrap_report = json.loads(bootstrap.stdout)
            self.assertEqual(bootstrap_report["bootstrap_source"], "spec")

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
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")
        self.assertEqual(report["current_focus"], "Recorded workflow stage: architect")
        self.assertEqual(report["suggested_workflow"], "architect")

    def test_next_bootstrap_can_seed_from_legacy_direction_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            legacy_dir = workspace / ".forge-artifacts" / "direction" / "workflow-workspace"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Workflow Workspace\n", encoding="utf-8")
            (legacy_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "recorded_at": "2026-04-02T00:00:00+00:00",
                        "project": "Workflow Workspace",
                        "profile": "solo-internal",
                        "intent": "BUILD",
                        "current_stage": "brainstorm",
                        "required_stage_chain": ["brainstorm", "plan", "build"],
                        "stage_name": "brainstorm",
                        "stage_status": "active",
                        "mode": "discovery-lite",
                        "decision_state": "direction-locked",
                        "activation_reason": "Legacy brainstorm state.",
                        "summary": "Choose the checkout hardening direction",
                        "notes": [],
                        "next_actions": ["Move into planning."],
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            bootstrap = run_python_script(
                "bootstrap_workflow_state.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Workflow Workspace",
                "--format",
                "json",
            )
            self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
            bootstrap_report = json.loads(bootstrap.stdout)
            self.assertEqual(bootstrap_report["bootstrap_source"], "direction-state")

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
        self.assertEqual(report["signals"]["workflow_state_source"], "workflow-state")
        self.assertEqual(report["current_focus"], "Recorded workflow stage: brainstorm")
        self.assertEqual(report["suggested_workflow"], "brainstorm")


if __name__ == "__main__":
    unittest.main()
