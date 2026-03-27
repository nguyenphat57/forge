from __future__ import annotations

import json
import unittest

from support import expected_output_contract

import common  # noqa: E402


class PreferencesCompatTests(unittest.TestCase):
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
            {"communication": {"language": "en"}},
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
