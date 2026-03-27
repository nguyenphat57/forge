from __future__ import annotations

import json
import unittest

from support import (
    expected_output_contract,
    forge_home_fixture,
    run_python_script,
    workspace_fixture,
)

import common  # noqa: E402


class PreferencesTests(unittest.TestCase):
    @staticmethod
    def expected_extra(expected: dict[str, object]) -> dict[str, object]:
        compat = common.load_preferences_compat()
        return common.merge_extra_preferences(common.compat_default_extra(compat), expected)

    @staticmethod
    def mojibake(value: str) -> str:
        return value.encode("utf-8").decode("latin-1")

    def test_missing_workspace_preferences_fall_back_to_defaults(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("no_preferences"),
            forge_home=forge_home_fixture("empty"),
        )

        self.assertEqual(report["source"]["type"], "defaults")
        self.assertEqual(
            report["preferences"],
            {
                "technical_level": "basic",
                "detail_level": "balanced",
                "autonomy_level": "balanced",
                "pace": "balanced",
                "feedback_style": "balanced",
                "personality": "default",
            },
        )
        self.assertEqual(report["extra"], self.expected_extra({}))
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
            {
                "technical_level": "technical",
                "detail_level": "concise",
                "autonomy_level": "autonomous",
                "pace": "fast",
                "feedback_style": "direct",
                "personality": "strict-coach",
            },
        )
        self.assertEqual(report["extra"], self.expected_extra({}))
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
            extra_path = common.resolve_global_extra_preferences_path(forge_home)
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
            self.assertEqual(report["extra"]["language"], "en")
            self.assertEqual(report["extra"]["orthography"], "plain_english")

    def test_load_preferences_repairs_mojibake_extra_preferences(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            forge_home = Path(temp_dir) / "forge-home"
            preferences_path = common.resolve_global_preferences_path(forge_home)
            extra_path = common.resolve_global_extra_preferences_path(forge_home)
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
            self.assertEqual(report["extra"]["tone_detail"], "Gọi Sếp, xưng Em")
            self.assertEqual(
                report["extra"]["custom_rules"],
                [
                    "Luôn dùng TypeScript thay vì JavaScript.",
                    "Luôn sử dụng ; thay vì && cho PowerShell.",
                ],
            )
            self.assertEqual(report["output_contract"], expected_output_contract(report["extra"]))
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
            self.assertEqual(report["extra"]["language"], "en")
            self.assertFalse((legacy_path.parent / "extra_preferences.json").exists())
            self.assertFalse((legacy_path.parent / "preferences.json.legacy.bak").exists())

    def test_global_preferences_take_precedence_over_workspace_legacy(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("preferences_workspace"),
            forge_home=forge_home_fixture("global_preferences"),
        )
        style = common.resolve_response_style(report["preferences"])

        self.assertEqual(report["source"]["type"], "global")
        self.assertEqual(report["extra"], self.expected_extra({}))
        self.assertEqual(report["preferences"]["technical_level"], "technical")
        self.assertEqual(report["preferences"]["personality"], "strict-coach")
        self.assertEqual(style["teaching_mode"], "best-practice-first")

    def test_workspace_legacy_preferences_still_override_defaults_when_no_global_exists(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("preferences_workspace"),
            forge_home=forge_home_fixture("empty"),
        )
        style = common.resolve_response_style(report["preferences"])
        contract = common.resolve_output_contract(report["extra"])

        self.assertEqual(report["source"]["type"], "workspace-legacy")
        self.assertEqual(
            report["preferences"],
            {
                "technical_level": "newbie",
                "detail_level": "detailed",
                "autonomy_level": "autonomous",
                "pace": "fast",
                "feedback_style": "direct",
                "personality": "mentor",
            },
        )
        self.assertEqual(
            report["extra"],
            self.expected_extra(
                {
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
                }
            ),
        )
        self.assertEqual(style["terminology_mode"], "translated")
        self.assertEqual(style["response_verbosity"], "detailed")
        self.assertEqual(style["decision_mode"], "propose-best-path-and-execute-safe-slices")
        self.assertEqual(style["delivery_pace"], "fast")
        self.assertEqual(style["feedback_mode"], "direct")
        self.assertEqual(style["teaching_mode"], "explain-why")
        self.assertEqual(contract, expected_output_contract(report["extra"]))
        self.assertEqual(contract["language"], "en")
        self.assertEqual(contract["orthography"], "plain-english")
        self.assertEqual(contract["tone_detail"], "Address the user as lead engineer.")

    def test_invalid_preferences_warn_and_fall_back_in_non_strict_mode(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("invalid_preferences_workspace"),
            forge_home=forge_home_fixture("empty"),
        )

        self.assertEqual(report["source"]["type"], "workspace-legacy")
        self.assertEqual(report["extra"], self.expected_extra({"unknown_field": "ignored"}))
        self.assertEqual(report["preferences"]["technical_level"], "basic")
        self.assertEqual(report["preferences"]["detail_level"], "balanced")
        self.assertEqual(report["preferences"]["autonomy_level"], "guided")
        self.assertEqual(report["preferences"]["pace"], "steady")
        self.assertEqual(report["preferences"]["feedback_style"], "gentle")
        self.assertEqual(report["preferences"]["personality"], "strict-coach")
        self.assertTrue(any("technical_level" in warning for warning in report["warnings"]))
        self.assertTrue(any("detail_level" in warning for warning in report["warnings"]))

    def test_invalid_preferences_raise_in_strict_mode(self) -> None:
        with self.assertRaises(ValueError):
            common.load_preferences(
                workspace=workspace_fixture("invalid_preferences_workspace"),
                strict=True,
                forge_home=forge_home_fixture("empty"),
            )

    def test_extras_extracted_from_compat_payload(self) -> None:
        compat_path = common.PREFERENCES_COMPAT_PATH
        if not compat_path.exists():
            self.skipTest(f"preferences-compat.json not available at {compat_path}")
        compat = json.loads(compat_path.read_text(encoding="utf-8"))
        payload = {
            "communication": {
                "persona": "mentor",
                "tone": "friendly",
                "language": "en",
                "orthography": "plain_english",
            },
            "technical": {
                "technical_level": "technical",
                "detail_level": "learning",
                "autonomy": "autonomous",
                "quality": "production_ready",
            },
            "working_style": {
                "pace": "fast",
                "feedback": "direct",
            },
            "custom_rules": [
                "Always log every action before guessing a root cause.",
            ],
        }

        extras = common.extract_extras(payload, compat_config=compat)

        self.assertEqual(
            extras,
            {
                "language": "en",
                "orthography": "plain_english",
                "output_quality": "production_ready",
                "custom_rules": [
                    "Always log every action before guessing a root cause.",
                ],
                "communication": {
                    "tone": "friendly",
                },
            },
        )
        contract = common.resolve_output_contract(extras)
        self.assertEqual(contract, expected_output_contract(extras))
        self.assertEqual(contract["language"], "en")
        self.assertEqual(contract["orthography"], "plain-english")

    def test_resolve_output_contract_supports_generic_language(self) -> None:
        contract = common.resolve_output_contract({"language": "en"})

        self.assertEqual(contract, expected_output_contract({"language": "en"}))

    def test_resolve_output_contract_normalizes_generic_orthography(self) -> None:
        contract = common.resolve_output_contract({"orthography": "plain_english"})

        self.assertEqual(contract, expected_output_contract({"orthography": "plain_english"}))
        self.assertEqual(contract["orthography"], "plain-english")

    def test_resolve_extra_preferences_applies_compat_defaults(self) -> None:
        compat_path = common.PREFERENCES_COMPAT_PATH
        if not compat_path.exists():
            self.skipTest(f"preferences-compat.json not available at {compat_path}")
        compat = json.loads(compat_path.read_text(encoding="utf-8"))

        defaults_only = common.resolve_extra_preferences(None, compat_config=compat)
        overridden = common.resolve_extra_preferences(
            {
                "communication": {
                    "language": "en",
                }
            },
            compat_config=compat,
        )

        self.assertEqual(defaults_only, common.compat_default_extra(compat))
        self.assertEqual(overridden["language"], "en")
        default_orthography = common.compat_default_extra(compat).get("orthography")
        if default_orthography is not None:
            self.assertEqual(overridden["orthography"], default_orthography)

    def test_serialize_preferences_payload_keeps_new_writes_flat_without_existing_legacy_payload(self) -> None:
        compat_path = common.PREFERENCES_COMPAT_PATH
        if not compat_path.exists():
            self.skipTest(f"preferences-compat.json not available at {compat_path}")
        compat = json.loads(compat_path.read_text(encoding="utf-8"))
        serialized = common.serialize_preferences_payload(
            {
                "technical_level": "basic",
                "detail_level": "balanced",
                "autonomy_level": "balanced",
                "pace": "balanced",
                "feedback_style": "balanced",
                "personality": "mentor",
            },
            existing_payload=None,
            replace=False,
            extra_updates={
                "language": "en",
                "orthography": "plain_english",
                "output_quality": "production_ready",
                "custom_rules": [
                    "Always log every action before guessing a root cause.",
                ],
            },
            compat_config=compat,
        )

        self.assertEqual(serialized["technical_level"], "basic")
        self.assertEqual(serialized["language"], "en")
        self.assertEqual(serialized["orthography"], "plain_english")
        self.assertEqual(serialized["output_quality"], "production_ready")
        self.assertEqual(
            serialized["custom_rules"],
            [
                "Always log every action before guessing a root cause.",
            ],
        )
        self.assertIsNone(common.get_nested_value(serialized, "communication.language"))

    def test_serialize_preferences_payload_updates_existing_legacy_compat_payload(self) -> None:
        compat_path = common.PREFERENCES_COMPAT_PATH
        if not compat_path.exists():
            self.skipTest(f"preferences-compat.json not available at {compat_path}")
        compat = json.loads(compat_path.read_text(encoding="utf-8"))
        existing_payload = {
            "communication": {
                "persona": "assistant",
                "tone": "friendly",
                "language": "en",
            },
            "technical": {
                "technical_level": "basic",
                "detail_level": "simple",
                "autonomy": "ask_often",
                "quality": "production",
            },
            "working_style": {
                "pace": "careful",
                "feedback": "gentle",
            },
            "custom_rules": [],
        }

        serialized = common.serialize_preferences_payload(
            {
                "technical_level": "basic",
                "detail_level": "balanced",
                "autonomy_level": "balanced",
                "pace": "balanced",
                "feedback_style": "balanced",
                "personality": "mentor",
            },
            existing_payload=existing_payload,
            replace=False,
            extra_updates={
                "language": "en",
                "orthography": "plain_english",
                "output_quality": "production_ready",
                "custom_rules": [
                    "Always log every action before guessing a root cause.",
                ],
            },
            compat_config=compat,
        )

        self.assertEqual(common.get_nested_value(serialized, "communication.language"), "en")
        self.assertEqual(common.get_nested_value(serialized, "communication.orthography"), "plain_english")
        self.assertEqual(common.get_nested_value(serialized, "technical.quality"), "production_ready")
        self.assertEqual(common.get_nested_value(serialized, "technical.detail_level"), "simple")
        self.assertEqual(common.get_nested_value(serialized, "working_style.feedback"), "gentle")
        self.assertEqual(
            common.get_nested_value(serialized, "custom_rules"),
            [
                "Always log every action before guessing a root cause.",
            ],
        )

    def test_resolve_preferences_script_reports_global_payload(self) -> None:
        result = run_python_script(
            "resolve_preferences.py",
            "--workspace",
            str(workspace_fixture("no_preferences")),
            "--format",
            "json",
            env={"FORGE_HOME": str(forge_home_fixture("global_preferences"))},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source"]["type"], "global")
        self.assertEqual(report["preferences"]["technical_level"], "technical")
        self.assertEqual(report["preferences"]["pace"], "fast")
        self.assertEqual(report["extra"], self.expected_extra({}))
        self.assertEqual(report["response_style"]["teaching_mode"], "best-practice-first")

    def test_resolve_preferences_script_warns_for_invalid_workspace_payload(self) -> None:
        result = run_python_script(
            "resolve_preferences.py",
            "--workspace",
            str(workspace_fixture("invalid_preferences_workspace")),
            "--format",
            "json",
            env={"FORGE_HOME": str(forge_home_fixture("empty"))},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "WARN")
        self.assertGreaterEqual(len(report["warnings"]), 1)
        self.assertEqual(report["preferences"]["personality"], "strict-coach")
        self.assertEqual(report["preferences"]["feedback_style"], "gentle")
        self.assertEqual(report["extra"], self.expected_extra({"unknown_field": "ignored"}))

    def test_resolve_preferences_includes_workspace_extras(self) -> None:
        result = run_python_script(
            "resolve_preferences.py",
            "--workspace",
            str(workspace_fixture("preferences_workspace")),
            "--format",
            "json",
            env={"FORGE_HOME": str(forge_home_fixture("global_preferences"))},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source"]["type"], "global")
        self.assertEqual(
            report["extra"],
            self.expected_extra(
                {
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
                }
            ),
        )
        self.assertEqual(report["output_contract"], expected_output_contract(report["extra"]))
        self.assertEqual(report["output_contract"]["language"], "en")
        self.assertEqual(report["output_contract"]["orthography"], "plain-english")


if __name__ == "__main__":
    unittest.main()
