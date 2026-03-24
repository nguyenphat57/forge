from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import FIXTURES_DIR, run_python_script, workspace_fixture


class BumpWorkflowTests(unittest.TestCase):
    def test_bump_preview_cases(self) -> None:
        cases = json.loads((FIXTURES_DIR / "bump_cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                result = run_python_script(
                    "prepare_bump.py",
                    "--workspace",
                    str(workspace_fixture(case["workspace_fixture"])),
                    "--bump",
                    case["bump"],
                    "--format",
                    "json",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)

                self.assertEqual(report["status"], case["expected_status"])
                self.assertEqual(report["current_version"], case["expected_current_version"])
                self.assertEqual(report["target_version"], case["expected_target_version"])

    def test_bump_apply_updates_version_and_changelog(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "VERSION").write_text("1.4.2\n", encoding="utf-8")
            (workspace / "CHANGELOG.md").write_text("# Changelog\n\n## 1.4.2 - 2026-03-01\n\n- Existing.\n", encoding="utf-8")

            result = run_python_script(
                "prepare_bump.py",
                "--workspace",
                str(workspace),
                "--bump",
                "patch",
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["target_version"], "1.4.3")
            self.assertEqual((workspace / "VERSION").read_text(encoding="utf-8").strip(), "1.4.3")
            changelog = (workspace / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## 1.4.3 - ", changelog)


if __name__ == "__main__":
    unittest.main()
