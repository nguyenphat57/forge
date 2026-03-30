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
            self.assertTrue((workspace / ".forge-artifacts" / "changes" / "active" / slug / "resume.md").exists())
            self.assertTrue((workspace / ".forge-artifacts" / "changes" / "active" / slug / "specs" / slug / "spec.md").exists())

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
            self.assertTrue(Path(archive_report["resume_path"]).exists())
            self.assertEqual(archive_report["change"]["state"], "archived")
            self.assertIn("archived_from", archive_report["change"])
            self.assertTrue((workspace / ".brain" / "decisions.json").exists())
            self.assertTrue((workspace / ".brain" / "learnings.json").exists())
            self.assertTrue((workspace / "docs" / "specs" / "change-index.json").exists())
            decisions = json.loads((workspace / ".brain" / "decisions.json").read_text(encoding="utf-8"))
            learnings = json.loads((workspace / ".brain" / "learnings.json").read_text(encoding="utf-8"))
            spec_index = json.loads((workspace / "docs" / "specs" / "change-index.json").read_text(encoding="utf-8"))
            self.assertEqual(decisions[0]["status"], "resolved")
            self.assertEqual(learnings[0]["status"], "resolved")
            self.assertTrue(decisions[0]["evidence"][0].startswith("Archived change:"))
            self.assertEqual(spec_index[0]["slug"], slug)

    def test_capture_continuity_defaults_to_resolved_with_resume_hint(self) -> None:
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
                "--next",
                "Re-open release notes before widening the compatibility window",
                "--brain-dir",
                str(brain_dir),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            entries = json.loads((brain_dir / "decisions.json").read_text(encoding="utf-8"))

        self.assertEqual(report["entry"]["status"], "resolved")
        self.assertEqual(report["entry"]["resume_hint"], "Re-open release notes before widening the compatibility window")
        self.assertEqual(entries[0]["status"], "resolved")
        self.assertEqual(entries[0]["resume_hint"], "Re-open release notes before widening the compatibility window")
        self.assertEqual(entries[0]["summary"], "Compatibility window must stay one release")

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
