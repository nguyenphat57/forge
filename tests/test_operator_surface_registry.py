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

        self.assertNotIn("resume", repo_actions)
        self.assertNotIn("bootstrap", repo_actions)
        self.assertNotIn("delegate", repo_actions)
        self.assertNotIn("capture-continuity", repo_actions)
        self.assertNotIn("help", repo_actions)
        self.assertNotIn("next", repo_actions)
        self.assertNotIn("run", repo_actions)
        self.assertNotIn("help", host_actions)
        self.assertNotIn("next", host_actions)
        self.assertNotIn("run", host_actions)
        self.assertNotIn("bootstrap", host_actions)
        self.assertNotIn("capture-continuity", host_actions)

    def test_operator_surface_contract_sets_stay_closed(self) -> None:
        core_registry = load_core_registry()
        codex_registry = load_bundle_registry("forge-codex")
        antigravity_registry = load_bundle_registry("forge-antigravity")

        self.assertEqual(
            set(core_registry["repo_operator_surface"]["actions"]),
            set(),
        )
        self.assertEqual(set(core_registry["repo_operator_surface"]["session_modes"]), set())
        self.assertEqual(
            set(core_registry["host_operator_surface"]["actions"]),
            set(),
        )
        self.assertEqual(set(core_registry["host_operator_surface"]["session_modes"]), set())
        self.assertEqual(
            set(codex_registry["host_operator_surface"]["actions"]),
            {"delegate"},
        )
        self.assertEqual(set(codex_registry["host_operator_surface"]["session_modes"]), set())
        self.assertEqual(
            set(antigravity_registry["host_operator_surface"]["actions"]),
            set(),
        )
        self.assertEqual(set(antigravity_registry["host_operator_surface"]["session_modes"]), set())

    def test_current_docs_spine_stays_closed(self) -> None:
        current_docs = {path.name for path in (ROOT_DIR / "docs" / "current").glob("*.md")}
        self.assertEqual(
            current_docs,
            {
                "architecture.md",
                "constitution-lite.md",
                "install-and-activation.md",
                "kernel-tooling.md",
                "operator-surface.md",
                "smoke-test-checklist.md",
                "smoke-tests.md",
                "target-state.md",
            },
        )

    def test_codex_overlay_registry_keeps_session_surface_primary_only(self) -> None:
        registry = load_bundle_registry("forge-codex")

        self.assertNotIn("intents", registry)
        self.assertNotIn("session_modes", registry)
        self.assertEqual(
            registry["host_operator_surface"]["actions"]["delegate"]["primary_aliases_by_host"],
            {},
        )
        self.assertEqual(registry["skill_catalog"]["session-management"]["owner"], "forge-session-management")
        self.assertNotIn("bootstrap", registry["host_operator_surface"]["actions"])

    def test_antigravity_overlay_registry_keeps_natural_language_session_surface(self) -> None:
        registry = load_bundle_registry("forge-antigravity")
        session = registry["skill_catalog"]["session-management"]

        self.assertNotIn("intents", registry)
        self.assertNotIn("session_modes", registry)
        self.assertEqual(session["owner"], "forge-session-management")
        self.assertTrue(session["session_modes"]["restore"]["natural_language_examples_by_host"]["antigravity"])

    def test_generated_operator_surface_docs_reflect_registry_posture(self) -> None:
        repo_surface = (ROOT_DIR / "docs" / "current" / "operator-surface.md").read_text(encoding="utf-8")
        codex_surface = (ROOT_DIR / "packages" / "forge-codex" / "overlay" / "docs" / "codex-operator-surface.md").read_text(encoding="utf-8")
        antigravity_surface = (ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "docs" / "antigravity-operator-surface.md").read_text(encoding="utf-8")
        antigravity_global = (ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "GEMINI.global.md").read_text(encoding="utf-8")

        self.assertNotIn("`bootstrap`", repo_surface)
        self.assertNotIn("`delegate`", repo_surface)
        self.assertNotIn("`capture-continuity`", repo_surface)
        self.assertNotIn("scripts/resolve_help_next.py", repo_surface)
        self.assertNotIn("repo_operator.py help", repo_surface)
        self.assertNotIn("repo_operator.py next", repo_surface)
        self.assertNotIn("repo_operator.py run", repo_surface)
        self.assertNotIn("repo_operator.py bump", repo_surface)
        self.assertIn("forge-bump-release", repo_surface)
        self.assertNotIn("scripts/session_context.py", repo_surface)
        self.assertNotIn("scripts/bootstrap_workflow_state.py", repo_surface)
        self.assertNotIn("/delegate", codex_surface)
        self.assertNotIn("Optional aliases:", codex_surface)
        self.assertNotIn("bootstrap", codex_surface)
        self.assertNotIn("capture-continuity", codex_surface)
        self.assertNotIn("/save-brain", codex_surface)
        self.assertIn("## Natural-Language Session Requests", antigravity_surface)
        self.assertNotIn("/delegate", antigravity_surface)
        self.assertNotIn("Optional aliases:", antigravity_surface)
        self.assertNotIn("bootstrap", antigravity_surface)
        self.assertNotIn("capture-continuity", antigravity_surface)
        self.assertNotIn("/recap", antigravity_surface)
        self.assertIn("save context", antigravity_surface)
        self.assertIn("Session requests stay natural-language", antigravity_global)
        self.assertNotIn("/recap", antigravity_global)
        self.assertNotIn("Primary operator aliases:", antigravity_global)
        self.assertNotIn("Compatibility aliases:", antigravity_global)

    def test_pre_2_15_historical_plan_surface_is_pruned(self) -> None:
        plan_docs = {path.name for path in (ROOT_DIR / "docs" / "plans").glob("*.md")}

        self.assertEqual(
            plan_docs,
            {
                "2026-04-23-docs-specs-pre-2-15-cleanup-implementation-plan.md",
                "2026-04-23-retired-help-next-run-command-cleanup-implementation-plan.md",
                "2026-04-23-runtime-ownership-refactor-implementation-plan.md",
                "2026-04-23-skill-local-command-ownership-implementation-plan.md",
            },
        )
        self.assertFalse((ROOT_DIR / "docs" / "archive").exists())
        self.assertFalse((ROOT_DIR / "docs" / "specs").exists())

    def test_current_docs_do_not_target_superseded_roadmaps(self) -> None:
        target_state = (ROOT_DIR / "docs" / "current" / "target-state.md").read_text(encoding="utf-8")
        operator_surface = (ROOT_DIR / "docs" / "current" / "operator-surface.md").read_text(encoding="utf-8")

        self.assertIn("Current Contract Closure", target_state)
        self.assertIn("## Source Repo", operator_surface)
        self.assertIn("forge-bump-release", operator_surface)
        self.assertNotIn("Active roadmap tranche for the current kernel-only contraction line", target_state)
        self.assertNotIn("docs/plans/2026-04-11-forge-slim-refactor-v2.md", target_state)
        self.assertNotIn("docs/archive", target_state)
        self.assertNotIn("docs/archive", operator_surface)


if __name__ == "__main__":
    unittest.main()
