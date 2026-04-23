from __future__ import annotations

import json
import unittest

from support import expected_output_contract, forge_home_fixture, run_python_script, workspace_fixture

import common  # noqa: E402
from preferences_test_support import PreferencesTestSupport


class PreferencesLoadingTests(PreferencesTestSupport, unittest.TestCase):
    def test_missing_workspace_preferences_fall_back_to_defaults(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("no_preferences"),
            forge_home=forge_home_fixture("empty"),
        )

        self.assertEqual(report["source"]["type"], "defaults")
        self.assertEqual(
            report["preferences"],
            self.expected_extra(
                {
                    "technical_level": "basic",
                    "detail_level": "balanced",
                    "autonomy_level": "balanced",
                    "pace": "balanced",
                    "feedback_style": "balanced",
                    "personality": "default",
                }
            ),
        )
        self.assertEqual(report["warnings"], [])

    def test_global_preferences_override_defaults(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("no_preferences"),
            forge_home=forge_home_fixture("global_preferences"),
        )
        style = common.resolve_response_style(report["preferences"])

        self.assertEqual(report["source"]["type"], "global")
        self.assertEqual(
            report["preferences"],
            self.expected_extra(
                {
                    "technical_level": "technical",
                    "detail_level": "concise",
                    "autonomy_level": "autonomous",
                    "pace": "fast",
                    "feedback_style": "direct",
                    "personality": "strict-coach",
                }
            ),
        )
        self.assertEqual(report["sources"]["technical_level"], "global")
        self.assertEqual(style["terminology_mode"], "standard")
        self.assertEqual(style["response_verbosity"], "concise")
        self.assertEqual(style["decision_mode"], "propose-best-path-and-execute-safe-slices")
        self.assertEqual(style["delivery_pace"], "fast")
        self.assertEqual(style["feedback_mode"], "direct")
        self.assertEqual(style["teaching_mode"], "best-practice-first")

    def test_explicit_preferences_file_reads_split_extra_sibling(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            forge_home = Path(temp_dir) / "forge-home"
            preferences_path = common.resolve_global_preferences_path(forge_home)
            extra_path = common.resolve_legacy_global_extra_preferences_path(forge_home)
            preferences_path.parent.mkdir(parents=True, exist_ok=True)
            preferences_path.write_text(
                json.dumps(
                    {
                        "technical_level": "technical",
                        "detail_level": "concise",
                        "autonomy_level": "autonomous",
                        "pace": "fast",
                        "feedback_style": "direct",
                        "personality": "strict-coach",
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

            report = common.load_preferences(preferences_file=preferences_path, forge_home=forge_home)

            self.assertEqual(report["source"]["type"], "explicit")
            self.assertEqual(report["preferences"]["technical_level"], "technical")
            self.assertEqual(report["preferences"]["language"], "en")
            self.assertEqual(report["preferences"]["orthography"], "plain_english")
            self.assertEqual(report["sources"]["language"], "explicit")

    def test_explicit_legacy_extra_preferences_file_is_rejected(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            forge_home = Path(temp_dir) / "forge-home"
            extra_path = common.resolve_legacy_global_extra_preferences_path(forge_home)
            extra_path.parent.mkdir(parents=True, exist_ok=True)
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

            with self.assertRaisesRegex(ValueError, "Legacy extra preferences files are migration input only"):
                common.load_preferences(preferences_file=extra_path, forge_home=forge_home)

    def test_load_preferences_repairs_mojibake_extra_preferences(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            forge_home = Path(temp_dir) / "forge-home"
            preferences_path = common.resolve_global_preferences_path(forge_home)
            extra_path = common.resolve_legacy_global_extra_preferences_path(forge_home)
            preferences_path.parent.mkdir(parents=True, exist_ok=True)
            preferences_path.write_text(
                json.dumps(
                    {
                        "technical_level": "basic",
                        "detail_level": "detailed",
                        "autonomy_level": "balanced",
                        "pace": "balanced",
                        "feedback_style": "direct",
                        "personality": "mentor",
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
                        "language": "vi",
                        "orthography": "vietnamese_diacritics",
                        "tone_detail": self.mojibake("Gọi Sếp, xưng Em"),
                        "custom_rules": [
                            self.mojibake("Luôn dùng TypeScript thay vì JavaScript."),
                            self.mojibake("Luôn sử dụng ; thay vì && cho PowerShell."),
                        ],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            report = common.load_preferences(
                workspace=workspace_fixture("no_preferences"),
                forge_home=forge_home,
            )

            self.assertEqual(report["source"]["type"], "global")
            self.assertEqual(report["preferences"]["tone_detail"], "Gọi Sếp, xưng Em")
            self.assertEqual(
                report["preferences"]["custom_rules"],
                [
                    "Luôn dùng TypeScript thay vì JavaScript.",
                    "Luôn sử dụng ; thay vì && cho PowerShell.",
                ],
            )
            self.assertEqual(report["output_contract"], expected_output_contract(report["preferences"]))
            self.assertEqual(report["output_contract"]["tone_detail"], "Gọi Sếp, xưng Em")

    def test_resolve_preferences_explicit_legacy_file_is_read_only(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            legacy_path = Path(temp_dir) / "preferences.json"
            legacy_path.write_text(
                json.dumps(
                    {
                        "technical_level": "basic",
                        "detail_level": "balanced",
                        "autonomy_level": "balanced",
                        "pace": "balanced",
                        "feedback_style": "direct",
                        "personality": "default",
                        "language": "en",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_python_script(
                "resolve_preferences.py",
                "--preferences-file",
                str(legacy_path),
                "--format",
                "json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["preferences"]["language"], "en")
            self.assertFalse((legacy_path.parent / "extra_preferences.json").exists())
            self.assertFalse((legacy_path.parent / "preferences.json.legacy.bak").exists())

    def test_workspace_preferences_override_global_per_key(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("preferences_workspace"),
            forge_home=forge_home_fixture("global_preferences"),
        )
        style = common.resolve_response_style(report["preferences"])

        self.assertEqual(report["source"]["type"], "merged")
        self.assertEqual(report["preferences"]["technical_level"], "newbie")
        self.assertEqual(report["preferences"]["personality"], "mentor")
        self.assertEqual(report["preferences"]["language"], "en")
        self.assertEqual(report["sources"]["technical_level"], "workspace")
        self.assertEqual(report["sources"]["language"], "workspace")
        self.assertEqual(style["teaching_mode"], "explain-why")

    def test_workspace_preferences_override_defaults_when_no_global_exists(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("preferences_workspace"),
            forge_home=forge_home_fixture("empty"),
        )
        style = common.resolve_response_style(report["preferences"])
        contract = common.resolve_output_contract(report["preferences"])

        self.assertEqual(report["source"]["type"], "workspace")
        self.assertEqual(
            report["preferences"],
            {
                "technical_level": "newbie",
                "detail_level": "detailed",
                "autonomy_level": "autonomous",
                "pace": "fast",
                "feedback_style": "direct",
                "personality": "mentor",
                "tone_detail": "Address the user as lead engineer.",
                "language": "en",
                "orthography": "plain_english",
                "output_quality": "production_ready",
                "custom_rules": [
                    "Keep each file under 300 lines unless a split would reduce clarity.",
                    "Keep one responsibility per file and avoid overlapping concerns.",
                    "Prefer TypeScript over JavaScript.",
                    "Prefer PowerShell over Command Prompt on Windows.",
                    "Use semicolons in PowerShell examples instead of shell chaining operators.",
                    "Log observable evidence before guessing a root cause.",
                ],
            },
        )
        self.assertEqual(style["terminology_mode"], "translated")
        self.assertEqual(style["response_verbosity"], "detailed")
        self.assertEqual(style["decision_mode"], "propose-best-path-and-execute-safe-slices")
        self.assertEqual(style["delivery_pace"], "fast")
        self.assertEqual(style["feedback_mode"], "direct")
        self.assertEqual(style["teaching_mode"], "explain-why")
        self.assertEqual(contract, expected_output_contract(report["preferences"]))
        self.assertEqual(contract["language"], "en")
        self.assertEqual(contract["orthography"], "plain-english")
        self.assertEqual(contract["tone_detail"], "Address the user as lead engineer.")

    def test_invalid_preferences_warn_and_fall_back_in_non_strict_mode(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("invalid_preferences_workspace"),
            forge_home=forge_home_fixture("empty"),
        )

        self.assertEqual(report["source"]["type"], "workspace")
        self.assertEqual(report["preferences"]["technical_level"], "basic")
        self.assertEqual(report["preferences"]["detail_level"], "balanced")
        self.assertEqual(report["preferences"]["autonomy_level"], "guided")
        self.assertEqual(report["preferences"]["pace"], "steady")
        self.assertEqual(report["preferences"]["feedback_style"], "gentle")
        self.assertEqual(report["preferences"]["personality"], "strict-coach")
        self.assertTrue(any("technical_level" in warning for warning in report["warnings"]))
        self.assertTrue(any("detail_level" in warning for warning in report["warnings"]))
        self.assertTrue(any("unknown_field" in warning for warning in report["warnings"]))

    def test_invalid_preferences_raise_in_strict_mode(self) -> None:
        with self.assertRaises(ValueError):
            common.load_preferences(
                workspace=workspace_fixture("invalid_preferences_workspace"),
                strict=True,
                forge_home=forge_home_fixture("empty"),
            )

    def test_load_preferences_keeps_legacy_delegation_marker_as_custom_rule(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
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
                        "custom_rules": [
                            "Delegated: Spawn subagents để tăng tiến độ khi cần",
                        ],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            report = common.load_preferences(
                workspace=workspace_fixture("no_preferences"),
                forge_home=forge_home,
            )

        self.assertIn(
            "Delegated: Spawn subagents để tăng tiến độ khi cần",
            report["preferences"]["custom_rules"],
        )
        self.assertNotIn("legacy_delegation_rule_detected", report["warnings"])


if __name__ == "__main__":
    unittest.main()
