from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class SessionContextBoundaryTests(unittest.TestCase):
    def test_save_writes_session_without_decision_learning_or_error_sidecars(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "save",
                "--workspace",
                str(workspace),
                "--task",
                "Capture operator contract",
                "--decision",
                "Save context remains a session snapshot",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            session = json.loads((workspace / ".brain" / "session.json").read_text(encoding="utf-8"))

            brain_dir = workspace / ".brain"
            self.assertEqual(session["decisions_made"], ["Save context remains a session snapshot"])
            self.assertFalse((brain_dir / "decisions.json").exists())
            self.assertFalse((brain_dir / "learnings.json").exists())
            self.assertFalse((brain_dir / "errors.json").exists())

    def test_closeout_learning_is_durable_without_raw_error_record(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "closeout",
                "--workspace",
                str(workspace),
                "--learning",
                "Operator context contract needs explicit persistence boundaries",
                "--evidence",
                "docs/current/operator-surface.md",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            learnings = json.loads((workspace / ".brain" / "learnings.json").read_text(encoding="utf-8"))

            self.assertEqual(report["continuity_action"], "saved")
            self.assertIsNone(report["session_file"])
            self.assertIsNone(report["handover_file"])
            self.assertEqual(learnings[0]["kind"], "learning")
            self.assertFalse((workspace / ".brain" / "errors.json").exists())

    def test_raw_error_is_not_a_session_context_persistence_mode(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "README.md").write_text("# Checkout Workspace\n", encoding="utf-8")

            result = run_python_script(
                "session_context.py",
                "closeout",
                "--workspace",
                str(workspace),
                "--error",
                "Traceback: boom",
                "--format",
                "json",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unrecognized arguments: --error", result.stderr)
            self.assertFalse((workspace / ".brain").exists())


if __name__ == "__main__":
    unittest.main()
