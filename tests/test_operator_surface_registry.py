from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from operator_surface_support import load_bundle_registry  # noqa: E402


class OperatorSurfaceRegistryTests(unittest.TestCase):
    def test_codex_overlay_registry_keeps_session_surface_primary_only(self) -> None:
        registry = load_bundle_registry("forge-codex")

        self.assertEqual(registry["intents"]["SESSION"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["restore"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["save"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["handover"]["shortcuts"], [])
        self.assertEqual(
            registry["operator_surface"]["actions"]["delegate"]["primary_aliases_by_host"]["codex"],
            ["/delegate"],
        )
        self.assertEqual(
            registry["operator_surface"]["session_modes"]["restore"]["compatibility_aliases_by_host"],
            {},
        )

    def test_antigravity_overlay_registry_keeps_compatibility_aliases_with_deprecation(self) -> None:
        registry = load_bundle_registry("forge-antigravity")
        surface = registry["operator_surface"]["session_modes"]

        self.assertEqual(registry["intents"]["SESSION"]["shortcuts"], ["/recap", "/save-brain", "/handover"])
        self.assertEqual(registry["session_modes"]["restore"]["shortcuts"], ["/recap", "/recap full", "/recap deep"])
        self.assertEqual(registry["session_modes"]["save"]["shortcuts"], ["/save-brain"])
        self.assertEqual(registry["session_modes"]["handover"]["shortcuts"], ["/handover"])
        self.assertEqual(surface["restore"]["compatibility_aliases_by_host"]["antigravity"], ["/recap"])
        self.assertEqual(surface["save"]["compatibility_aliases_by_host"]["antigravity"], ["/save-brain"])
        self.assertEqual(surface["handover"]["compatibility_aliases_by_host"]["antigravity"], ["/handover"])
        for mode_name in ("restore", "save", "handover"):
            with self.subTest(mode=mode_name):
                self.assertEqual(surface[mode_name]["deprecation_line"], "1 stable line")

    def test_generated_operator_surface_docs_reflect_registry_posture(self) -> None:
        codex_surface = (ROOT_DIR / "packages" / "forge-codex" / "overlay" / "references" / "codex-operator-surface.md").read_text(encoding="utf-8")
        antigravity_surface = (ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "references" / "antigravity-operator-surface.md").read_text(encoding="utf-8")
        antigravity_global = (ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "GEMINI.global.md").read_text(encoding="utf-8")

        self.assertIn("/delegate", codex_surface)
        self.assertNotIn("/save-brain", codex_surface)
        self.assertIn("## Compatibility Wrappers", antigravity_surface)
        self.assertIn("/recap", antigravity_surface)
        self.assertIn("one stable line", antigravity_surface)
        compatibility_section = antigravity_global.split("Compatibility aliases:", maxsplit=1)[1]
        self.assertIn("/recap", compatibility_section)
        self.assertIn("/save-brain", compatibility_section)
        primary_section = antigravity_global.split("Primary operator aliases:", maxsplit=1)[1].split("Compatibility aliases:", maxsplit=1)[0]
        self.assertNotIn("/recap", primary_section)
        self.assertNotIn("/save-brain", primary_section)

    def test_plan_doc_is_maintenance_safe(self) -> None:
        plan_path = ROOT_DIR / "docs" / "plans" / "PLAN.md"
        text = plan_path.read_text(encoding="utf-8")

        self.assertIn("Status: implemented", text)
        self.assertNotIn("\ufffd", text)
        self.assertTrue(any(char in text for char in "ặếộự"))


if __name__ == "__main__":
    unittest.main()
