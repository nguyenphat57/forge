from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import load_json_fixture, run_python_script, workspace_fixture


class InitializeWorkspaceTests(unittest.TestCase):
    def test_initialize_workspace_preview_cases(self) -> None:
        for case in load_json_fixture("workspace_init_cases.json"):
            with self.subTest(case=case["name"]):
                workspace = workspace_fixture(case["workspace_fixture"])
                result = run_python_script(
                    "initialize_workspace.py",
                    "--workspace",
                    str(workspace),
                    "--format",
                    "json",
                    *case["args"],
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)

                self.assertEqual(report["workspace_mode"], case["expected_mode"])
                self.assertEqual(report["recommended_next_workflow"], case["expected_next_workflow"])

    def test_initialize_workspace_apply_creates_expected_structure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "greenfield"
            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Forge Demo",
                "--seed-preferences",
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["workspace_mode"], "greenfield")
            self.assertTrue((workspace / ".brain" / "session.json").exists())
            self.assertTrue((workspace / ".brain" / "preferences.json").exists())
            self.assertTrue((workspace / "docs" / "plans").exists())
            self.assertTrue((workspace / "docs" / "specs").exists())

    def test_initialize_workspace_existing_mode_reuses_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Existing\n", encoding="utf-8")

            first = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            second = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            report = json.loads(second.stdout)

            self.assertEqual(report["workspace_mode"], "existing")
            self.assertGreaterEqual(len(report["reused_paths"]), 1)


if __name__ == "__main__":
    unittest.main()
