from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import expected_output_contract, forge_home_fixture, load_json_fixture, run_python_script, workspace_fixture

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

    def test_write_preferences_script_apply_writes_unified_global_file(self) -> None:
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
                "--language",
                "en",
                "--orthography",
                "plain_english",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            written_path = common.resolve_global_preferences_path(forge_home)
            written = json.loads(written_path.read_text(encoding="utf-8"))
            self.assertEqual(written["technical_level"], "newbie")
            self.assertEqual(written["pace"], "fast")
            self.assertEqual(written["feedback_style"], "direct")
            self.assertEqual(written["language"], "en")
            self.assertEqual(written["orthography"], "plain_english")
            self.assertFalse(common.resolve_legacy_global_extra_preferences_path(forge_home).exists())
            self.assertEqual(report["output_contract"], expected_output_contract(report["preferences"]))
            self.assertEqual(report["output_contract"]["language"], "en")
            self.assertEqual(report["output_contract"]["orthography"], "plain-english")

    def test_write_preferences_script_apply_workspace_scope_creates_sparse_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
                "--scope",
                "workspace",
                "--language",
                "en",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            workspace_path = common.resolve_workspace_preferences_path(workspace)
            written = json.loads(workspace_path.read_text(encoding="utf-8"))
            self.assertEqual(written, {"language": "en"})
            self.assertEqual(report["targets"], [str(workspace_path)])
            self.assertEqual(report["preferences"]["language"], "en")
            self.assertEqual(report["sources"]["language"], "workspace")

    def test_write_preferences_script_apply_both_writes_global_and_workspace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
                "--scope",
                "both",
                "--pace",
                "fast",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            global_written = json.loads(common.resolve_global_preferences_path(forge_home).read_text(encoding="utf-8"))
            workspace_written = json.loads(common.resolve_workspace_preferences_path(workspace).read_text(encoding="utf-8"))
            self.assertEqual(global_written, {"pace": "fast"})
            self.assertEqual(workspace_written, {"pace": "fast"})
            self.assertEqual(len(report["targets"]), 2)
            self.assertEqual(report["sources"]["pace"], "workspace")

    def test_write_preferences_script_rejects_removed_delegation_preference_flag(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
                "--delegation-preference",
                "review-lanes",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertNotEqual(result.returncode, 0)

            self.assertFalse(common.resolve_global_preferences_path(forge_home).exists())

    def test_write_preferences_script_migrates_legacy_split_global_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            forge_home = Path(temp_dir) / "forge-home"
            preferences_path = common.resolve_global_preferences_path(forge_home)
            extra_path = common.resolve_legacy_global_extra_preferences_path(forge_home)
            preferences_path.parent.mkdir(parents=True, exist_ok=True)
            preferences_path.write_text(
                json.dumps(
                    {
                        "technical_level": "basic",
                        "detail_level": "balanced",
                        "autonomy_level": "balanced",
                        "pace": "balanced",
                        "feedback_style": "balanced",
                        "personality": "default",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            extra_path.write_text(
                json.dumps(
                    {
                        "language": "en",
                        "orthography": "plain_english",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
                "--pace",
                "fast",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            written = json.loads(preferences_path.read_text(encoding="utf-8"))
            self.assertTrue(report["migrated_legacy_global_preferences"])
            self.assertEqual(written["pace"], "fast")
            self.assertEqual(written["language"], "en")
            self.assertEqual(written["orthography"], "plain_english")
            self.assertTrue((preferences_path.parent / "preferences.json.legacy.bak").exists())
            self.assertTrue((preferences_path.parent / "extra_preferences.json.legacy.bak").exists())
            self.assertFalse(extra_path.exists())

    def test_write_preferences_script_clear_field_restores_fallback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            forge_home = Path(temp_dir) / "forge-home"
            common.resolve_global_preferences_path(forge_home).parent.mkdir(parents=True, exist_ok=True)
            common.resolve_global_preferences_path(forge_home).write_text(
                json.dumps({"language": "vi"}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            common.resolve_workspace_preferences_path(workspace).parent.mkdir(parents=True, exist_ok=True)
            common.resolve_workspace_preferences_path(workspace).write_text(
                json.dumps({"language": "en"}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
                "--scope",
                "workspace",
                "--clear-field",
                "language",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["preferences"]["language"], "vi")
            self.assertEqual(report["sources"]["language"], "global")
            self.assertFalse(common.resolve_workspace_preferences_path(workspace).exists())

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
