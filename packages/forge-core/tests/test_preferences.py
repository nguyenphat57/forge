from __future__ import annotations

import json
import unittest

from support import ROOT_DIR, forge_home_fixture, run_python_script, workspace_fixture

import common  # noqa: E402


class PreferencesTests(unittest.TestCase):
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
        self.assertEqual(report["extra"], {})
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
        self.assertEqual(report["extra"], {})
        self.assertEqual(style["terminology_mode"], "standard")
        self.assertEqual(style["response_verbosity"], "concise")
        self.assertEqual(style["decision_mode"], "propose-best-path-and-execute-safe-slices")
        self.assertEqual(style["delivery_pace"], "fast")
        self.assertEqual(style["feedback_mode"], "direct")
        self.assertEqual(style["teaching_mode"], "best-practice-first")

    def test_global_preferences_take_precedence_over_workspace_legacy(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("preferences_workspace"),
            forge_home=forge_home_fixture("global_preferences"),
        )
        style = common.resolve_response_style(report["preferences"])

        self.assertEqual(report["source"]["type"], "global")
        self.assertEqual(report["extra"], {})
        self.assertEqual(report["preferences"]["technical_level"], "technical")
        self.assertEqual(report["preferences"]["personality"], "strict-coach")
        self.assertEqual(style["teaching_mode"], "best-practice-first")

    def test_workspace_legacy_preferences_still_override_defaults_when_no_global_exists(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("preferences_workspace"),
            forge_home=forge_home_fixture("empty"),
        )
        style = common.resolve_response_style(report["preferences"])

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
            {
                "tone_detail": "Gọi Sếp, xưng Em",
                "language": "vi",
                "output_quality": "production_ready",
                "custom_rules": [
                    "Mỗi file không được vượt quá 300 dòng, nếu vượt phải chia nhỏ ra",
                    "Mỗi file chỉ chứa một chức năng, không gộp hay chồng chéo chức năng vào 1 file",
                    "Luôn dùng TypeScript thay vì JavaScript",
                    "Luôn sử dụng PowerShell thay vì Command Prompt",
                    "Luôn sử dụng ; thay vì && cho PowerShell",
                    "Luôn debug log mọi hành động, không đoán mò lỗi",
                ],
            },
        )
        self.assertEqual(style["terminology_mode"], "translated")
        self.assertEqual(style["response_verbosity"], "detailed")
        self.assertEqual(style["decision_mode"], "propose-best-path-and-execute-safe-slices")
        self.assertEqual(style["delivery_pace"], "fast")
        self.assertEqual(style["feedback_mode"], "direct")
        self.assertEqual(style["teaching_mode"], "explain-why")

    def test_invalid_preferences_warn_and_fall_back_in_non_strict_mode(self) -> None:
        report = common.load_preferences(
            workspace=workspace_fixture("invalid_preferences_workspace"),
            forge_home=forge_home_fixture("empty"),
        )

        self.assertEqual(report["source"]["type"], "workspace-legacy")
        self.assertEqual(report["extra"], {"unknown_field": "ignored"})
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
        compat_path = ROOT_DIR.parent.parent / "packages" / "forge-antigravity" / "overlay" / "data" / "preferences-compat.json"
        compat = json.loads(compat_path.read_text(encoding="utf-8"))
        payload = {
            "communication": {
                "persona": "mentor",
                "tone": "friendly",
                "language": "vi",
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
                "communication": {
                    "tone": "friendly",
                    "language": "vi",
                },
                "technical": {
                    "quality": "production_ready",
                },
                "custom_rules": [
                    "Always log every action before guessing a root cause.",
                ],
            },
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
        self.assertEqual(report["extra"], {})
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
        self.assertEqual(report["extra"], {"unknown_field": "ignored"})

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
            {
                "tone_detail": "Gọi Sếp, xưng Em",
                "language": "vi",
                "output_quality": "production_ready",
                "custom_rules": [
                    "Mỗi file không được vượt quá 300 dòng, nếu vượt phải chia nhỏ ra",
                    "Mỗi file chỉ chứa một chức năng, không gộp hay chồng chéo chức năng vào 1 file",
                    "Luôn dùng TypeScript thay vì JavaScript",
                    "Luôn sử dụng PowerShell thay vì Command Prompt",
                    "Luôn sử dụng ; thay vì && cho PowerShell",
                    "Luôn debug log mọi hành động, không đoán mò lỗi",
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
