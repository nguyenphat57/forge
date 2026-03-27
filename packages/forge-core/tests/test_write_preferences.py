from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import expected_output_contract, forge_home_fixture, load_json_fixture, run_python_script, workspace_fixture

import common  # noqa: E402


class WritePreferencesTests(unittest.TestCase):
    @staticmethod
    def read_persisted_extra(
        preferences_payload: dict[str, object],
        extra_payload: dict[str, object] | None,
        field: str,
    ) -> object:
        if isinstance(extra_payload, dict):
            direct = extra_payload.get(field)
            if direct is not None:
                return direct

        direct = preferences_payload.get(field)
        if direct is not None:
            return direct

        compat_paths = {
            "language": "communication.language",
            "orthography": "communication.orthography",
        }
        compat_path = compat_paths.get(field)
        if compat_path is None:
            return None
        payload = extra_payload if isinstance(extra_payload, dict) else preferences_payload
        return common.get_nested_value(payload, compat_path)

    @staticmethod
    def expected_changed_extra_fields(*, language: str, orthography: str) -> list[str]:
        compat = common.load_preferences_compat()
        defaults = common.compat_default_extra(compat)
        changed: list[str] = []
        if defaults.get("language") != language:
            changed.append("language")
        if defaults.get("orthography") != orthography:
            changed.append("orthography")
        return changed

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
            written_path = common.resolve_global_preferences_path(forge_home)
            written = json.loads(written_path.read_text(encoding="utf-8"))
            reloaded = common.load_preferences(
                preferences_file=written_path,
                forge_home=forge_home,
            )

            self.assertIsInstance(written, dict)
            self.assertEqual(reloaded["preferences"], report["preferences"])
            self.assertEqual(reloaded["warnings"], [])

    def test_write_preferences_script_apply_writes_extra_fields(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "write_preferences.py",
                "--workspace",
                str(workspace),
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
            written_extra_path = common.resolve_global_extra_preferences_path(forge_home)
            written_extra = json.loads(written_extra_path.read_text(encoding="utf-8"))
            reloaded = common.load_preferences(
                preferences_file=written_path,
                forge_home=forge_home,
            )

            self.assertEqual(report["changed_fields"], [])
            self.assertEqual(
                report["changed_extra_fields"],
                self.expected_changed_extra_fields(
                    language="en",
                    orthography="plain_english",
                ),
            )
            self.assertEqual(report["extra"]["language"], "en")
            self.assertEqual(report["extra"]["orthography"], "plain_english")
            self.assertEqual(report["output_contract"], expected_output_contract(report["extra"]))
            self.assertEqual(report["output_contract"]["language"], "en")
            self.assertEqual(report["output_contract"]["orthography"], "plain-english")
            self.assertNotIn("language", written)
            self.assertNotIn("orthography", written)
            self.assertEqual(self.read_persisted_extra(written, written_extra, "language"), "en")
            self.assertEqual(self.read_persisted_extra(written, written_extra, "orthography"), "plain_english")
            self.assertEqual(reloaded["extra"]["language"], "en")
            self.assertEqual(reloaded["extra"]["orthography"], "plain_english")

    def test_write_preferences_script_preserves_existing_top_level_extras(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            forge_home = Path(temp_dir) / "forge-home"
            written_path = common.resolve_global_preferences_path(forge_home)
            written_path.parent.mkdir(parents=True, exist_ok=True)
            written_path.write_text(
                json.dumps(
                    {
                        "technical_level": "basic",
                        "detail_level": "balanced",
                        "autonomy_level": "balanced",
                        "pace": "balanced",
                        "feedback_style": "balanced",
                        "personality": "default",
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
            written = json.loads(written_path.read_text(encoding="utf-8"))
            written_extra_path = common.resolve_global_extra_preferences_path(forge_home)
            written_extra = json.loads(written_extra_path.read_text(encoding="utf-8"))

            self.assertEqual(report["preferences"]["pace"], "fast")
            self.assertEqual(report["extra"]["language"], "en")
            self.assertEqual(report["extra"]["orthography"], "plain_english")
            self.assertEqual(self.read_persisted_extra(written, written_extra, "language"), "en")
            self.assertEqual(self.read_persisted_extra(written, written_extra, "orthography"), "plain_english")
            self.assertTrue(written_extra_path.exists())
            self.assertTrue((written_path.parent / "preferences.json.legacy.bak").exists())
            self.assertTrue(report["migrated_legacy_global_preferences"])

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
