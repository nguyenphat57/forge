from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import forge_home_fixture, load_json_fixture, run_python_script, workspace_fixture

import common  # noqa: E402


class WritePreferencesTests(unittest.TestCase):
    def test_write_preferences_script_preview_cases(self) -> None:
        for case in load_json_fixture("preferences_write_cases.json"):
            with self.subTest(case=case["name"]):
                workspace = workspace_fixture(case["workspace_fixture"])
                result = run_python_script(
                    "write_preferences.py",
                    "--workspace",
                    str(workspace),
                    "--format",
                    "json",
                    *case["args"],
                    env={"FORGE_HOME": str(forge_home_fixture(case.get("forge_home_fixture", "empty")))},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)

                self.assertEqual(report["status"], case["expected_status"])
                self.assertEqual(report["preferences"], case["expected_preferences"])
                self.assertEqual(report["changed_fields"], case["expected_changed_fields"])
                self.assertFalse(report["applied"])

    def test_write_preferences_script_apply_writes_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
                "--technical-level",
                "beginner",
                "--pace",
                "fast",
                "--feedback-style",
                "direct",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["preferences"]["technical_level"], "newbie")
            self.assertEqual(report["preferences"]["pace"], "fast")
            self.assertEqual(report["preferences"]["feedback_style"], "direct")
            written = json.loads(common.resolve_global_preferences_path(forge_home).read_text(encoding="utf-8"))
            self.assertEqual(written, report["preferences"])

    def test_write_preferences_requires_updates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                temp_dir,
                "--format",
                "json",
                env={"FORGE_HOME": str(Path(temp_dir) / "forge-home")},
            )
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
