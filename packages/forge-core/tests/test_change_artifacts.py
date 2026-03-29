from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class ChangeArtifactsTests(unittest.TestCase):
    def test_start_status_and_archive_flow_updates_brain_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            started = run_python_script(
                "change_artifacts.py",
                "start",
                "Add offline checkout retry",
                "--workspace",
                str(workspace),
                "--task",
                "Implement retry state machine",
                "--format",
                "json",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            started_report = json.loads(started.stdout)
            slug = started_report["change"]["slug"]

            updated = run_python_script(
                "change_artifacts.py",
                "status",
                "--workspace",
                str(workspace),
                "--slug",
                slug,
                "--state",
                "in-progress",
                "--verified",
                "pytest tests/test_retry.py",
                "--residual-risk",
                "Need live browser verification",
                "--format",
                "json",
            )
            self.assertEqual(updated.returncode, 0, updated.stderr)
            updated_report = json.loads(updated.stdout)
            self.assertEqual(updated_report["change"]["state"], "in-progress")

            archived = run_python_script(
                "change_artifacts.py",
                "archive",
                "--workspace",
                str(workspace),
                "--slug",
                slug,
                "--decision",
                "Retry state machine uses persisted attempt count.",
                "--learning",
                "Browser verification is still needed for offline flows.",
                "--format",
                "json",
            )
            self.assertEqual(archived.returncode, 0, archived.stderr)
            archive_report = json.loads(archived.stdout)

            self.assertTrue(Path(archive_report["archive_root"]).exists())
            self.assertTrue((workspace / ".brain" / "decisions.json").exists())
            self.assertTrue((workspace / ".brain" / "learnings.json").exists())

    def test_guard_blocks_destructive_action(self) -> None:
        result = run_python_script(
            "change_artifacts.py",
            "guard",
            "Clean up broken workspace",
            "--action",
            "git reset --hard",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["classification"], "block")


if __name__ == "__main__":
    unittest.main()
