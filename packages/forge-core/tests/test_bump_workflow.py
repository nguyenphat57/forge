from __future__ import annotations

import json
import subprocess
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

    def test_bump_auto_infers_minor_from_new_capability_file_in_git_workspace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "VERSION").write_text("1.4.2\n", encoding="utf-8")
            (workspace / "CHANGELOG.md").write_text("# Changelog\n\n## 1.4.2 - 2026-03-01\n\n- Existing.\n", encoding="utf-8")

            for command in (
                ["git", "init"],
                ["git", "config", "user.name", "Forge Tests"],
                ["git", "config", "user.email", "forge-tests@example.com"],
                ["git", "add", "VERSION", "CHANGELOG.md"],
                ["git", "commit", "-m", "release: 1.4.2"],
            ):
                completed = subprocess.run(
                    command,
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            workflow_dir = workspace / "packages" / "forge-codex" / "overlay" / "workflows" / "execution"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            (workflow_dir / "dispatch-subagents.md").write_text(
                "# Dispatch Subagents\n\n- New capability.\n",
                encoding="utf-8",
            )

            result = run_python_script(
                "prepare_bump.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["selected_bump"], "minor")
            self.assertEqual(report["bump_source"], "inferred")
            self.assertEqual(report["inference_confidence"], "high")
            self.assertEqual(report["target_version"], "1.5.0")
            self.assertEqual(report["inferred_from"], "since-last-version-change")
            self.assertIn(
                "packages/forge-codex/overlay/workflows/execution/dispatch-subagents.md",
                report["analysis_changed_files"],
            )

    def test_bump_auto_warns_when_git_context_is_unavailable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "VERSION").write_text("1.4.2\n", encoding="utf-8")
            (workspace / "CHANGELOG.md").write_text("# Changelog\n\n## 1.4.2 - 2026-03-01\n\n- Existing.\n", encoding="utf-8")

            result = run_python_script(
                "prepare_bump.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["status"], "WARN")
            self.assertEqual(report["selected_bump"], "patch")
            self.assertEqual(report["bump_source"], "inferred")
            self.assertEqual(report["inference_confidence"], "low")
            self.assertEqual(report["target_version"], "1.4.3")
            self.assertEqual(report["inferred_from"], "no-git-context")
            self.assertTrue(any("Git context unavailable" in warning for warning in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
