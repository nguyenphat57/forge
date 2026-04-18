from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from operator_surface_support import load_bundle_registry, load_core_registry  # noqa: E402


class OperatorSurfaceRegistryTests(unittest.TestCase):
    def test_core_registry_splits_repo_and_host_operator_surfaces(self) -> None:
        registry = load_core_registry()
        repo_actions = registry["repo_operator_surface"]["actions"]
        host_actions = registry["host_operator_surface"]["actions"]

        self.assertIn("resume", repo_actions)
        self.assertNotIn("bootstrap", repo_actions)
        self.assertNotIn("delegate", repo_actions)
        self.assertNotIn("capture-continuity", repo_actions)
        self.assertIn("help", host_actions)
        self.assertNotIn("bootstrap", host_actions)
        self.assertNotIn("capture-continuity", host_actions)

    def test_operator_surface_contract_sets_stay_closed(self) -> None:
        core_registry = load_core_registry()
        codex_registry = load_bundle_registry("forge-codex")
        antigravity_registry = load_bundle_registry("forge-antigravity")

        self.assertEqual(
            set(core_registry["repo_operator_surface"]["actions"]),
            {"resume", "save", "handover", "help", "next", "run", "bump", "rollback", "customize", "init"},
        )
        self.assertEqual(set(core_registry["repo_operator_surface"]["session_modes"]), set())
        self.assertEqual(
            set(core_registry["host_operator_surface"]["actions"]),
            {"help", "next", "run", "bump", "rollback", "customize", "init"},
        )
        self.assertEqual(set(core_registry["host_operator_surface"]["session_modes"]), {"restore", "save", "handover"})
        self.assertEqual(
            set(codex_registry["host_operator_surface"]["actions"]),
            {"help", "next", "run", "delegate", "bump", "rollback", "customize", "init"},
        )
        self.assertEqual(set(codex_registry["host_operator_surface"]["session_modes"]), {"restore", "save", "handover"})
        self.assertEqual(
            set(antigravity_registry["host_operator_surface"]["actions"]),
            {"help", "next", "run", "bump", "rollback", "customize", "init"},
        )
        self.assertEqual(set(antigravity_registry["host_operator_surface"]["session_modes"]), {"restore", "save", "handover"})

    def test_current_docs_spine_stays_closed(self) -> None:
        current_docs = {path.name for path in (ROOT_DIR / "docs" / "current").glob("*.md")}
        self.assertEqual(current_docs, {"architecture.md", "install-and-activation.md", "operator-surface.md"})

    def test_codex_overlay_registry_keeps_session_surface_primary_only(self) -> None:
        registry = load_bundle_registry("forge-codex")

        self.assertEqual(registry["intents"]["SESSION"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["restore"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["save"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["handover"]["shortcuts"], [])
        self.assertEqual(
            registry["host_operator_surface"]["actions"]["delegate"]["primary_aliases_by_host"]["codex"],
            ["/delegate"],
        )
        self.assertEqual(
            registry["host_operator_surface"]["session_modes"]["restore"]["compatibility_aliases_by_host"],
            {},
        )
        self.assertNotIn("bootstrap", registry["host_operator_surface"]["actions"])

    def test_antigravity_overlay_registry_keeps_natural_language_session_surface(self) -> None:
        registry = load_bundle_registry("forge-antigravity")
        surface = registry["host_operator_surface"]["session_modes"]

        self.assertEqual(registry["intents"]["SESSION"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["restore"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["save"]["shortcuts"], [])
        self.assertEqual(registry["session_modes"]["handover"]["shortcuts"], [])
        for mode_name in ("restore", "save", "handover"):
            with self.subTest(mode=mode_name):
                self.assertEqual(surface[mode_name].get("compatibility_aliases_by_host"), {})
                self.assertIsNone(surface[mode_name].get("deprecation_line"))
                self.assertTrue(surface[mode_name]["natural_language_examples_by_host"]["antigravity"])

    def test_generated_operator_surface_docs_reflect_registry_posture(self) -> None:
        repo_surface = (ROOT_DIR / "docs" / "current" / "operator-surface.md").read_text(encoding="utf-8")
        codex_surface = (ROOT_DIR / "packages" / "forge-codex" / "overlay" / "references" / "codex-operator-surface.md").read_text(encoding="utf-8")
        antigravity_surface = (ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "references" / "antigravity-operator-surface.md").read_text(encoding="utf-8")
        antigravity_global = (ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "GEMINI.global.md").read_text(encoding="utf-8")

        self.assertNotIn("`bootstrap`", repo_surface)
        self.assertNotIn("`delegate`", repo_surface)
        self.assertNotIn("`capture-continuity`", repo_surface)
        self.assertNotIn("scripts/resolve_help_next.py", repo_surface)
        self.assertNotIn("scripts/session_context.py", repo_surface)
        self.assertNotIn("scripts/bootstrap_workflow_state.py", repo_surface)
        self.assertIn("/delegate", codex_surface)
        self.assertNotIn("bootstrap", codex_surface)
        self.assertNotIn("capture-continuity", codex_surface)
        self.assertNotIn("/save-brain", codex_surface)
        self.assertIn("## Natural-Language Session Requests", antigravity_surface)
        self.assertNotIn("/delegate", antigravity_surface)
        self.assertNotIn("bootstrap", antigravity_surface)
        self.assertNotIn("capture-continuity", antigravity_surface)
        self.assertNotIn("/recap", antigravity_surface)
        self.assertIn("save context", antigravity_surface)
        self.assertIn("Session requests stay natural-language", antigravity_global)
        self.assertNotIn("/recap", antigravity_global)
        primary_section = antigravity_global.split("Primary operator aliases:", maxsplit=1)[1].split("Session requests stay natural-language:", maxsplit=1)[0]
        self.assertNotIn("/save-brain", primary_section)

    def test_kernel_contraction_plan_is_historical_and_clean(self) -> None:
        roadmap_path = ROOT_DIR / "docs" / "plans" / "forge_refactor_V3.md"
        text = roadmap_path.read_text(encoding="utf-8")

        self.assertIn("Status: historical implemented contraction tranche", text)
        self.assertNotIn("Status: current roadmap", text)
        self.assertNotIn("\ufffd", text)
        self.assertIn("scripts/repo_operator.py", text)

    def test_current_reference_pointers_do_not_target_superseded_roadmaps(self) -> None:
        reference_map = (ROOT_DIR / "packages" / "forge-core" / "references" / "reference-map.md").read_text(encoding="utf-8")
        archive_index = (ROOT_DIR / "docs" / "archive" / "INDEX.md").read_text(encoding="utf-8")

        self.assertIn("maintenance-only posture", reference_map)
        self.assertNotIn("Active roadmap tranche for the current kernel-only contraction line", reference_map)
        self.assertNotIn("docs/plans/2026-04-11-forge-slim-refactor-v2.md", reference_map)
        self.assertIn("docs/plans/forge_refactor_V3.md", archive_index)
        self.assertNotIn("docs/plans/2026-04-11-forge-slim-refactor-v2.md", archive_index)
        self.assertNotIn("docs/plans/2026-04-02-forge-1.15.x-maintenance-closure.md` |", archive_index)


if __name__ == "__main__":
    unittest.main()
