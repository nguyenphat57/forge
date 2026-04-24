from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_release  # noqa: E402
import install_bundle  # noqa: E402


class ReleaseRepoTestSupport(unittest.TestCase):
    def assert_markdown_first_adapter_skill(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()
        self.assertIn("<extremely-important>", lowered, label)
        self.assertIn("</extremely-important>", lowered, label)
        self.assertIn("1% chance", lowered, label)
        self.assertIn("before any response or action", lowered, label)
        self.assertIn("restore personalization", lowered, label)
        self.assertIn("process skills first", lowered, label)
        self.assertIn("route_preview is not the current public contract", lowered, label)

        self.assertIn("sibling Forge skills", text, label)

    def assert_session_restores_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("adapter-global", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("forge-customize", text, label)
        self.assertIn("Response Personalization", text, label)

    def assert_codex_global_agents_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("Thread Bootstrap", text, label)
        self.assertIn("On every new thread, restore Forge response personalization", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("Preference owner skill", text, label)
        self.assertIn("forge-customize", text, label)
        self.assertIn("Preferences resolver owner command", text, label)

    def assert_antigravity_skill_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        self.assert_markdown_first_adapter_skill(path, label=label)

    def assert_antigravity_agent_prompt_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("restore preferences from Antigravity-global state at thread start", text, label)
        self.assertIn("default to Vietnamese with full diacritics unless resolved preferences say otherwise", text, label)

    def assert_antigravity_global_gemini_bootstraps_preferences(self, path: Path, *, label: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn("Preference owner skill", text, label)
        self.assertIn("forge-customize", text, label)
        self.assertIn("Preferences resolver owner command", text, label)
        self.assertIn("state/preferences.json", text, label)
        self.assertIn("read the preference file directly", text, label)

    def assert_routing_locale_config(self, path: Path, *, label: str) -> None:
        config = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("enabled_locales", config, label)
        self.assertIn("vi", config["enabled_locales"], label)

    def assert_output_contract_profiles(self, path: Path, *, label: str) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        vi = payload.get("languages", {}).get("vi", {})
        self.assertEqual(vi.get("default_orthography"), "vietnamese-diacritics", label)
        self.assertEqual(vi.get("contract", {}).get("accent_policy"), "required", label)
        self.assertEqual(
            payload.get("orthographies", {}).get("vietnamese-diacritics", {}).get("encoding"),
            "utf-8",
            label,
        )
