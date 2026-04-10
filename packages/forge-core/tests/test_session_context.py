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
        self.assertTrue(report["handover_file"].endswith(".brain\\handover.md") or report["handover_file"].endswith(".brain/handover.md"))
        self.assertIn("HANDOVER", handover)
        self.assertIn("Stabilize checkout rollout", handover)
        self.assertIn("Run browser QA", handover)
        self.assertEqual(report["best_next_step"], "Ship the browser QA findings into release note follow-up")
        self.assertIn("Ship the browser QA findings into release note follow-up", handover)

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
        self.assertEqual(report["mode"], "resume")
        self.assertEqual(report["current_stage"], "session-active")
        self.assertEqual(report["current_focus"], "Session task: Finish checkout retry slice")
        self.assertEqual(report["pending_work"], ["Run browser QA on checkout"])
        self.assertIn("Verification: pytest tests/test_checkout.py", report["relevant_continuity"])
        self.assertTrue(report["session_file"])
        self.assertTrue(report["handover_file"])

    def test_resume_can_fall_back_to_repo_state_without_saved_session(self) -> None:
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
        self.assertEqual(report["mode"], "resume")
        self.assertEqual(report["current_stage"], "planned")
        self.assertEqual(report["current_focus"], "Plan: Checkout rollback hardening")
        self.assertEqual(report["best_next_step"], "Start the first concrete slice from plan 'Checkout rollback hardening'.")
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
        self.assertEqual(report["current_focus"], "Gate approved: ready-for-merge")
        self.assertEqual(report["pending_work"], ["Proceed with the approved handoff for 'ready-for-merge'."])
        self.assertEqual(report["risks_or_assumptions"], [])
        self.assertTrue(
            any("Filtered 2 stale session item(s)" in warning for warning in report["warnings"]),
            report["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
