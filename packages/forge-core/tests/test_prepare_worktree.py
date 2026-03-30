from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")
    (path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True, encoding="utf-8")


class PrepareWorktreeTests(unittest.TestCase):
    def test_prepare_worktree_creates_project_local_worktree_and_runs_baseline(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            workspace.mkdir(parents=True, exist_ok=True)
            _init_repo(workspace)

            result = run_python_script(
                "prepare_worktree.py",
                "--workspace",
                str(workspace),
                "--name",
                "checkout",
                "--baseline-command",
                "python -c \"print('baseline ok')\"",
                "--persist",
                "--output-dir",
                str(workspace),
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["state"], "ready")
            self.assertTrue(Path(report["worktree_path"]).exists())
            self.assertTrue(report["ignore_safety"]["required"])
            exclude_text = (workspace / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("/.forge-artifacts/worktrees/", exclude_text)

    def test_prepare_worktree_blocks_on_failing_baseline(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            workspace.mkdir(parents=True, exist_ok=True)
            _init_repo(workspace)

            result = run_python_script(
                "prepare_worktree.py",
                "--workspace",
                str(workspace),
                "--name",
                "checkout-fail",
                "--baseline-command",
                "python -c \"import sys; sys.exit(2)\"",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["state"], "blocked")
            self.assertEqual(report["baseline_results"][0]["returncode"], 2)


if __name__ == "__main__":
    unittest.main()
