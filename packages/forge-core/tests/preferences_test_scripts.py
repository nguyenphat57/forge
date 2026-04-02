from __future__ import annotations

import json
import unittest

from support import expected_output_contract, forge_home_fixture, run_python_script, workspace_fixture

import common  # noqa: E402
from preferences_test_support import PreferencesTestSupport


class PreferencesScriptTests(PreferencesTestSupport, unittest.TestCase):
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
        self.assertEqual(report["extra"]["delegation_preference"], "auto")
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
        self.assertEqual(report["extra"]["delegation_preference"], "auto")

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
        self.assertNotIn("delegation_preference", report["output_contract"])

    def test_resolve_preferences_maps_legacy_delegation_marker_to_typed_field(self) -> None:
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

            result = run_python_script(
                "resolve_preferences.py",
                "--workspace",
                str(workspace_fixture("no_preferences")),
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(report["extra"]["delegation_preference"], "auto")
        self.assertIn("legacy_delegation_rule_detected", report["warnings"])
