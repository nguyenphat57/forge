from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class SessionContextTests(unittest.TestCase):
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

    def test_save_writes_session_json_with_explicit_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            (workspace / "src").mkdir(parents=True, exist_ok=True)
            (workspace / "src" / "checkout.ts").write_text("export const ready = true;\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--task",
                "Finish checkout retry slice",
                "--file",
                "src/checkout.ts",
                "--pending",
                "Re-run retry smoke",
                "--verification",
                "pytest tests/test_checkout.py",
                "--decision",
                "Retry state stays persisted across reloads",
                "--risk",
                "Browser QA still pending",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            session = json.loads((workspace / ".brain" / "session.json").read_text(encoding="utf-8"))

        self.assertEqual(report["mode"], "save")
        self.assertEqual(report["owner"], "forge-session-management")
        self.assertEqual(session["working_on"]["task"], "Finish checkout retry slice")
        self.assertEqual(session["working_on"]["files"], ["src/checkout.ts"])
        self.assertEqual(session["pending_tasks"], ["Re-run retry smoke"])
        self.assertEqual(session["verification"], ["pytest tests/test_checkout.py"])
        self.assertEqual(session["decisions_made"], ["Retry state stays persisted across reloads"])
        self.assertEqual(session["risks"], ["Browser QA still pending"])
        self.assertIsNone(report["handover_file"])

    def test_save_can_also_refresh_handover(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--task",
                "Stabilize checkout rollout",
                "--pending",
                "Run browser QA",
                "--next-step",
                "Ship the browser QA findings into release note follow-up",
                "--write-handover",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            handover = (workspace / ".brain" / "handover.md").read_text(encoding="utf-8")

        self.assertEqual(report["mode"], "save")
        self.assertEqual(report["owner"], "forge-session-management")
        self.assertTrue(report["handover_file"].endswith(".brain\\handover.md") or report["handover_file"].endswith(".brain/handover.md"))
        self.assertIn("HANDOVER", handover)
        self.assertIn("Stabilize checkout rollout", handover)
        self.assertIn("Run browser QA", handover)
        self.assertEqual(report["best_next_step"], "Ship the browser QA findings into release note follow-up")
        self.assertIn("Ship the browser QA findings into release note follow-up", handover)

    def test_closeout_without_durable_signals_skips_brain_creation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Tiny Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "closeout",
                "--workspace",
                str(workspace),
                "--task",
                "Answer a simple question",
                "--status",
                "completed",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(report["mode"], "closeout")
        self.assertEqual(report["owner"], "forge-session-management")
        self.assertEqual(report["continuity_action"], "skipped")
        self.assertFalse((workspace / ".brain").exists())

    def test_closeout_with_session_signals_writes_session_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "closeout",
                "--workspace",
                str(workspace),
                "--task",
                "Finish checkout retry slice",
                "--status",
                "completed",
                "--file",
                "src/checkout.ts",
                "--pending",
                "Run browser QA on checkout",
                "--verification",
                "pytest tests/test_checkout.py",
                "--risk",
                "Browser QA still pending",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            session = json.loads((workspace / ".brain" / "session.json").read_text(encoding="utf-8"))

        self.assertEqual(report["continuity_action"], "saved")
        self.assertEqual(session["working_on"]["task"], "Finish checkout retry slice")
        self.assertEqual(session["working_on"]["files"], ["src/checkout.ts"])
        self.assertEqual(session["pending_tasks"], ["Run browser QA on checkout"])
        self.assertEqual(session["verification"], ["pytest tests/test_checkout.py"])
        self.assertEqual(session["risks"], ["Browser QA still pending"])

    def test_closeout_with_blocker_writes_handover_automatically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "closeout",
                "--workspace",
                str(workspace),
                "--task",
                "Finish checkout retry slice",
                "--blocker",
                "Missing browser credentials for smoke test",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            handover = (workspace / ".brain" / "handover.md").read_text(encoding="utf-8")

        self.assertEqual(report["continuity_action"], "saved")
        self.assertTrue(report["handover_file"])
        self.assertIn("Missing browser credentials for smoke test", handover)

    def test_closeout_appends_learning_and_decision_with_dedupe(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            args = [
                "closeout",
                "--workspace",
                str(workspace),
                "--task",
                "Capture checkout continuity",
                "--learning",
                "Browser smoke needs credentials before Electron launch",
                "--decision",
                "Checkout retry state remains persisted across reloads",
                "--evidence",
                "pytest tests/test_checkout.py -> PASS",
                "--tag",
                "checkout",
                "--format",
                "json",
            ]

            first = run_python_script("session_context.py", *args)
            second = run_python_script("session_context.py", *args)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            decisions = json.loads((workspace / ".brain" / "decisions.json").read_text(encoding="utf-8"))
            learnings = json.loads((workspace / ".brain" / "learnings.json").read_text(encoding="utf-8"))

        self.assertEqual(len(decisions), 1)
        self.assertEqual(len(learnings), 1)
        self.assertEqual(decisions[0]["kind"], "decision")
        self.assertEqual(learnings[0]["kind"], "learning")
        self.assertEqual(decisions[0]["scope"], workspace.name)
        self.assertIn("pytest tests/test_checkout.py -> PASS", learnings[0]["evidence"])
        self.assertIn("checkout", decisions[0]["tags"])

    def test_resume_includes_relevant_learning_and_decision_continuity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            (workspace / ".brain").mkdir(parents=True, exist_ok=True)
            (workspace / ".brain" / "decisions.json").write_text(
                json.dumps(
                    [
                        {
                            "kind": "decision",
                            "scope": "checkout",
                            "summary": "Checkout retry state remains persisted across reloads",
                            "status": "resolved",
                            "evidence": ["pytest tests/test_checkout.py -> PASS"],
                            "next": ["Apply this when retry UI changes"],
                            "tags": ["checkout"],
                            "resume_hint": "Apply this when retry UI changes",
                        }
                    ],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (workspace / ".brain" / "learnings.json").write_text(
                json.dumps(
                    [
                        {
                            "kind": "learning",
                            "scope": "browser-smoke",
                            "summary": "Browser smoke needs credentials before Electron launch",
                            "status": "active",
                            "evidence": ["electron-smoke.err.log"],
                            "next": [],
                            "tags": ["smoke"],
                            "resume_hint": "Check credentials before launching smoke.",
                        }
                    ],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            resumed = run_python_script(
                "session_context.py",
                "resume",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            report = json.loads(resumed.stdout)

        continuity = "\n".join(report["relevant_continuity"])
        self.assertIn("Decision: Checkout retry state remains persisted across reloads", continuity)
        self.assertIn("Learning: Browser smoke needs credentials before Electron launch", continuity)

    def test_resume_restores_saved_session_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            saved = run_python_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--task",
                "Finish checkout retry slice",
                "--pending",
                "Run browser QA on checkout",
                "--verification",
                "pytest tests/test_checkout.py",
                "--decision",
                "Retry state stays persisted across reloads",
                "--write-handover",
                "--format",
                "json",
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)

            resumed = run_python_script(
                "session_context.py",
                "resume",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            report = json.loads(resumed.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["owner"], "forge-session-management")
        self.assertEqual(report["mode"], "resume")
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["current_focus"], "No active work slice detected from repo state.")
        self.assertEqual(report["pending_work"], ["Run browser QA on checkout"])
        self.assertIn("Verification: pytest tests/test_checkout.py", report["relevant_continuity"])
        self.assertTrue(report["session_file"])
        self.assertTrue(report["handover_file"])
        self.assertTrue(
            any("Session context is available only as continuity sidecar." in warning for warning in report["warnings"]),
            report["warnings"],
        )

    def test_resume_auto_seeds_plan_docs_into_canonical_workflow_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            (workspace / "docs" / "plans").mkdir(parents=True, exist_ok=True)
            (workspace / "docs" / "plans" / "checkout.md").write_text(
                "# Plan: Checkout rollback hardening\n\n- Validate retry path.\n",
                encoding="utf-8",
            )

            resumed = run_python_script(
                "session_context.py",
                "resume",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            report = json.loads(resumed.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["owner"], "forge-session-management")
        self.assertEqual(report["mode"], "resume")
        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["current_focus"], "Recorded workflow stage: plan")
        self.assertIn("Resume the recorded workflow stage 'plan'", report["best_next_step"])
        self.assertNotIn("bootstrap_workflow_state.py", report["best_next_step"])
        self.assertIn("plan:", " ".join(report["restored_from"]))

    def test_resume_filters_stale_session_follow_ups_when_repo_is_clean_and_synced(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            remote = root / "remote.git"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            self._init_synced_git_repo(workspace, remote)

            saved = run_python_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--task",
                "Finish checkout retry slice",
                "--status",
                "completed",
                "--pending",
                "Review remaining diff, then commit and push if approved",
                "--risk",
                "Repo changes are still uncommitted and unpushed.",
                "--format",
                "json",
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)

            state_dir = workspace / ".forge-artifacts" / "workflow-state" / "checkout-workspace"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "project": "Checkout Workspace",
                        "current_stage": "quality-gate",
                        "last_recorded_kind": "quality-gate",
                        "latest_gate": {
                            "kind": "quality-gate",
                            "project": "Checkout Workspace",
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

            resumed = run_python_script(
                "session_context.py",
                "resume",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            report = json.loads(resumed.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["current_stage"], "unscoped")
        self.assertEqual(report["current_focus"], "No active work slice detected from repo state.")
        self.assertIn("verify_repo.py --profile fast", report["pending_work"][0])
        self.assertEqual(report["risks_or_assumptions"], [])
        self.assertTrue(
            any("Filtered 2 stale session item(s)" in warning for warning in report["warnings"]),
            report["warnings"],
        )
        self.assertTrue(
            any("Filtered stale merge-ready workflow-state" in warning for warning in report["warnings"]),
            report["warnings"],
        )

    def test_save_drops_stale_merge_handoff_when_repo_is_clean_and_synced(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            remote = root / "remote.git"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")
            self._init_synced_git_repo(workspace, remote)

            (workspace / ".brain").mkdir(parents=True, exist_ok=True)
            (workspace / ".brain" / "session.json").write_text(
                json.dumps(
                    {
                        "updated_at": "2026-04-11T00:00:00+00:00",
                        "working_on": {
                            "feature": "checkout-release",
                            "task": "Ship checkout release",
                            "status": "active",
                            "files": ["README.md"],
                        },
                        "pending_tasks": ["Proceed with the approved handoff for 'ready-for-merge'."],
                        "verification": [],
                        "decisions_made": [],
                        "risks": [],
                        "blockers": [],
                        "source_artifacts": [],
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            state_dir = workspace / ".forge-artifacts" / "workflow-state" / "checkout-workspace"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "project": "Checkout Workspace",
                        "current_stage": "quality-gate",
                        "last_recorded_kind": "quality-gate",
                        "latest_gate": {
                            "kind": "quality-gate",
                            "project": "Checkout Workspace",
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

            saved = run_python_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)
            report = json.loads(saved.stdout)
            session = json.loads((workspace / ".brain" / "session.json").read_text(encoding="utf-8"))

        self.assertEqual(report["best_next_step"], None)
        self.assertEqual(session["pending_tasks"], [])
        self.assertEqual(session["working_on"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
