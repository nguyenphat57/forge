from __future__ import annotations

import json
import re

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport
import build_release  # noqa: E402
import install_bundle_host  # noqa: E402


class ReleaseRepoOverlayTests(ReleaseRepoTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        build_release.build_all()

    def test_overlay_registries_extend_core_static_contract_without_reintroducing_route_heuristics(self) -> None:
        core_registry = json.loads(
            (ROOT_DIR / "packages" / "forge-core" / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
        )

        for bundle_name in ("forge-antigravity", "forge-codex"):
            overlay_registry = json.loads(
                (
                    ROOT_DIR
                    / "packages"
                    / bundle_name
                    / "overlay"
                    / "data"
                    / "orchestrator-registry.json"
                ).read_text(encoding="utf-8")
            )
            self.assertNotIn("workflow_state_contract", overlay_registry)
            self.assertNotIn("workflow_priority", overlay_registry)
            self.assertNotIn("repo_operator_surface", overlay_registry)
            self.assertNotIn("intents", overlay_registry)
            self.assertNotIn("solo_profiles", overlay_registry)

        for bundle_name in ("forge-antigravity", "forge-codex"):
            with self.subTest(bundle=bundle_name):
                dist_registry = json.loads(
                    (ROOT_DIR / "dist" / bundle_name / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
                )
                self.assertEqual(dist_registry["workflow_state_contract"], core_registry["workflow_state_contract"])
                self.assertEqual(dist_registry["workflow_priority"], core_registry["workflow_priority"])
                self.assertEqual(dist_registry["repo_operator_surface"], core_registry["repo_operator_surface"])
                self.assertIn("host_operator_surface", dist_registry)
                self.assertIn("host_capabilities", dist_registry)

    def test_antigravity_release_bundle_no_longer_ships_route_preview_fixture_overlay(self) -> None:
        self.assertFalse(
            (
                ROOT_DIR
                / "packages"
                / "forge-antigravity"
                / "overlay"
                / "tests"
                / "fixtures"
                / "route_preview_cases.json"
            ).exists()
        )
        self.assertNotIn(
            "tests/fixtures/route_preview_cases.json",
            json.loads((ROOT_DIR / "dist" / "forge-antigravity" / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))["packaging"]["required_bundle_paths"],
        )

    def test_antigravity_wave_b_overlay_files_exist(self) -> None:
        overlay_root = ROOT_DIR / "packages" / "forge-antigravity" / "overlay"
        expected_files = [
            overlay_root / "GEMINI.global.md",
            overlay_root / "SKILL.delta.md",
            overlay_root / "SKILL.md",
            overlay_root / "agents" / "openai.yaml",
            overlay_root / "data" / "orchestrator-registry.json",
            overlay_root / "workflows" / "operator" / "customize.md",
            overlay_root / "workflows" / "operator" / "init.md",
            overlay_root / "workflows" / "operator" / "help.md",
            overlay_root / "workflows" / "operator" / "next.md",
            overlay_root / "workflows" / "operator" / "run.md",
            overlay_root / "workflows" / "operator" / "bump.md",
            overlay_root / "workflows" / "operator" / "rollback.md",
            overlay_root / "references" / "antigravity-operator-surface.md",
            overlay_root / "data" / "preferences-compat.json",
            overlay_root / "data" / "routing-locales.json",
            overlay_root / "data" / "routing-locales" / "vi.json",
            overlay_root / "data" / "output-contracts.json",
        ]
        for path in expected_files:
            with self.subTest(path=path):
                self.assertTrue(path.exists())

        skill = (overlay_root / "SKILL.md").read_text(encoding="utf-8")
        self.assert_markdown_first_adapter_skill(
            overlay_root / "SKILL.md",
            label="forge-antigravity overlay skill",
        )
        self.assertIn("forge-verification-before-completion", skill)
        self.assertIn("forge-finishing-a-development-branch", skill)
        self.assertNotIn("review-pack", skill)
        self.assertNotIn("release-readiness", skill)
        self.assertNotIn("adoption-check", skill)
        self.assert_antigravity_skill_bootstraps_preferences(overlay_root / "SKILL.md", label="forge-antigravity overlay skill")
        self.assert_antigravity_agent_prompt_bootstraps_preferences(
            overlay_root / "agents" / "openai.yaml",
            label="forge-antigravity overlay agent prompt",
        )
        self.assert_antigravity_global_gemini_bootstraps_preferences(
            overlay_root / "GEMINI.global.md",
            label="forge-antigravity overlay gemini",
        )
        gemini_text = (overlay_root / "GEMINI.global.md").read_text(encoding="utf-8")
        self.assertIn("GENERATED FILE", gemini_text)
        self.assertIn("natural-language first", gemini_text)
        self.assertNotIn("/customize", gemini_text)
        self.assertNotIn("/init", gemini_text)
        self.assertIn("save context", gemini_text)
        self.assertNotIn("There is no `/gate` alias", gemini_text)
        self.assertNotIn("Compatibility aliases:", gemini_text)
        self.assertNotIn("Primary operator aliases:", gemini_text)
        self.assertIn("Session requests stay natural-language:", gemini_text)
        self.assertNotIn("/recap", gemini_text)
        self.assertNotIn("/save-brain", gemini_text)

    def test_materialized_antigravity_wave_b_overlay_contract(self) -> None:
        dist_root = ROOT_DIR / "dist" / "forge-antigravity"
        self.assertTrue((dist_root / "GEMINI.global.md").exists())
        self.assertTrue((dist_root / "SKILL.md").exists())
        self.assertFalse((dist_root / "SKILL.delta.md").exists())
        self.assertTrue((dist_root / "agents" / "openai.yaml").exists())
        self.assertTrue((dist_root / "data" / "orchestrator-registry.json").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "help.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "next.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "run.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "rollback.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "customize.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "init.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "session.md").exists())
        self.assertFalse((dist_root / "workflows" / "operator" / "recap.md").exists())
        self.assertFalse((dist_root / "workflows" / "operator" / "save-brain.md").exists())
        self.assertFalse((dist_root / "workflows" / "operator" / "handover.md").exists())
        self.assertFalse((dist_root / "workflows" / "execution" / "session.md").exists())
        self.assertTrue((dist_root / "references" / "antigravity-operator-surface.md").exists())
        self.assertTrue((dist_root / "data" / "preferences-compat.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales" / "vi.json").exists())
        self.assertTrue((dist_root / "data" / "output-contracts.json").exists())
        self.assertFalse((dist_root / "tests" / "fixtures" / "route_preview_cases.json").exists())
        self.assertIn("GENERATED FILE", (dist_root / "GEMINI.global.md").read_text(encoding="utf-8"))
        build_manifest = json.loads((dist_root / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(build_manifest["state"]["dev_root"]["env_var"], "GEMINI_HOME")
        self.assertEqual(build_manifest["state"]["dev_root"]["path_relative"], "forge-antigravity")
        self.assertEqual(build_manifest["packaging"]["default_target_strategy"], "gemini_home_skill")
        self.assertIn("GEMINI.global.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("SKILL.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("agents/openai.yaml", build_manifest["packaging"]["required_bundle_paths"])
        self.assertNotIn("tests/fixtures/route_preview_cases.json", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("workflows/operator/help.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("workflows/operator/next.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("workflows/operator/run.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("workflows/operator/rollback.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertEqual(build_manifest["generated_artifacts"]["manifest_path"], "docs/architecture/host-artifacts-manifest.json")
        self.assertEqual(build_manifest["generated_artifacts"]["artifacts"][0]["name"], "forge-antigravity-global-gemini")
        self.assertEqual(build_manifest["generated_artifacts"]["artifacts"][0]["bundle_output"], "GEMINI.global.md")
        self.assertEqual(len(build_manifest["generated_artifacts"]["artifacts"][0]["source_sha256"]), 64)
        self.assertEqual(len(build_manifest["generated_artifacts"]["artifacts"][0]["output_sha256"]), 64)
        rendered = install_bundle_host.render_antigravity_global_gemini(
            (dist_root / "GEMINI.global.md").read_text(encoding="utf-8"),
            dist_root.parent,
            dist_root,
        )
        self.assertNotRegex(rendered, re.compile(r"\{\{[A-Z0-9_]+\}\}"))
        self.assert_antigravity_skill_bootstraps_preferences(
            dist_root / "SKILL.md",
            label="dist forge-antigravity skill",
        )
        self.assert_antigravity_agent_prompt_bootstraps_preferences(
            dist_root / "agents" / "openai.yaml",
            label="dist forge-antigravity agent prompt",
        )
        self.assert_antigravity_global_gemini_bootstraps_preferences(
            dist_root / "GEMINI.global.md",
            label="dist forge-antigravity gemini",
        )
        rendered_gemini = (dist_root / "GEMINI.global.md").read_text(encoding="utf-8")
        self.assertIn("Session requests stay natural-language:", rendered_gemini)
        self.assertNotIn("/recap", rendered_gemini)
        self.assertNotIn("/customize", rendered_gemini)
        self.assertNotIn("/init", rendered_gemini)
        self.assertNotIn("Compatibility aliases:", rendered_gemini)
        self.assertNotIn("Primary operator aliases:", rendered_gemini)
        self.assert_routing_locale_config(dist_root / "data" / "routing-locales.json", label="dist forge-antigravity")
        self.assert_output_contract_profiles(dist_root / "data" / "output-contracts.json", label="dist forge-antigravity")
        self.assert_session_restores_preferences(
            dist_root / "workflows" / "operator" / "session.md",
            label="dist forge-antigravity session",
        )

    def test_codex_wave_c_overlay_files_exist(self) -> None:
        overlay_root = ROOT_DIR / "packages" / "forge-codex" / "overlay"
        expected_files = [
            overlay_root / "AGENTS.global.md",
            overlay_root / "SKILL.delta.md",
            overlay_root / "SKILL.md",
            overlay_root / "data" / "orchestrator-registry.json",
            overlay_root / "data" / "routing-locales.json",
            overlay_root / "data" / "routing-locales" / "vi.json",
            overlay_root / "data" / "output-contracts.json",
            overlay_root / "references" / "smoke-tests.md",
            overlay_root / "references" / "smoke-test-checklist.md",
            overlay_root / "workflows" / "execution" / "dispatch-subagents.md",
            overlay_root / "workflows" / "operator" / "session.md",
            overlay_root / "workflows" / "operator" / "help.md",
            overlay_root / "workflows" / "operator" / "next.md",
            overlay_root / "workflows" / "operator" / "run.md",
            overlay_root / "workflows" / "operator" / "bump.md",
            overlay_root / "workflows" / "operator" / "rollback.md",
            overlay_root / "workflows" / "operator" / "customize.md",
            overlay_root / "workflows" / "operator" / "init.md",
            overlay_root / "references" / "codex-operator-surface.md",
        ]
        for path in expected_files:
            with self.subTest(path=path):
                self.assertTrue(path.exists())

        skill = (overlay_root / "SKILL.md").read_text(encoding="utf-8")
        self.assert_markdown_first_adapter_skill(
            overlay_root / "SKILL.md",
            label="forge-codex overlay skill",
        )
        self.assertIn("AGENTS.md", skill)
        self.assertIn("delegate", skill)
        self.assertIn("forge-verification-before-completion", skill)
        self.assertIn("forge-finishing-a-development-branch", skill)
        self.assertNotIn("review-pack", skill)
        self.assertNotIn("release-readiness", skill)
        self.assertNotIn("adoption-check", skill)
        self.assertNotIn("save-brain", skill)
        self.assert_codex_global_agents_bootstraps_preferences(
            overlay_root / "AGENTS.global.md",
            label="forge-codex overlay agents",
        )
        agents_text = (overlay_root / "AGENTS.global.md").read_text(encoding="utf-8")
        self.assertIn("GENERATED FILE", agents_text)
        self.assertIn("natural-language first", agents_text)
        self.assertNotIn("/customize", agents_text)
        self.assertNotIn("/init", agents_text)
        self.assertNotIn("/delegate", agents_text)
        self.assertNotIn("Compatibility aliases:", agents_text)
        self.assertNotIn("Operator aliases:", agents_text)
        self.assertNotIn("/save-brain", (overlay_root / "workflows" / "operator" / "session.md").read_text(encoding="utf-8"))
        codex_surface = (overlay_root / "references" / "codex-operator-surface.md").read_text(encoding="utf-8")
        self.assertNotIn("/delegate", codex_surface)
        self.assertNotIn("/save-brain", codex_surface)
        self.assert_session_restores_preferences(
            overlay_root / "workflows" / "operator" / "session.md",
            label="forge-codex overlay session",
        )

    def test_materialized_codex_wave_c_overlay_contract(self) -> None:
        dist_root = ROOT_DIR / "dist" / "forge-codex"
        self.assertTrue((dist_root / "AGENTS.global.md").exists())
        self.assertTrue((dist_root / "SKILL.md").exists())
        self.assertFalse((dist_root / "SKILL.delta.md").exists())
        self.assertTrue((dist_root / "data" / "orchestrator-registry.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales" / "vi.json").exists())
        self.assertTrue((dist_root / "data" / "output-contracts.json").exists())
        self.assertTrue((dist_root / "references" / "smoke-tests.md").exists())
        self.assertTrue((dist_root / "references" / "smoke-test-checklist.md").exists())
        self.assertTrue((dist_root / "workflows" / "execution" / "dispatch-subagents.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "session.md").exists())
        self.assertFalse((dist_root / "workflows" / "execution" / "session.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "customize.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "init.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "help.md").exists())
        self.assertTrue((dist_root / "references" / "codex-operator-surface.md").exists())
        self.assertIn("GENERATED FILE", (dist_root / "AGENTS.global.md").read_text(encoding="utf-8"))
        build_manifest = json.loads((dist_root / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(build_manifest["state"]["dev_root"]["env_var"], "CODEX_HOME")
        self.assertEqual(build_manifest["state"]["dev_root"]["path_relative"], "forge-codex")
        self.assertEqual(build_manifest["packaging"]["default_target_strategy"], "codex_home_skill")
        self.assertIn("AGENTS.global.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("SKILL.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("references/smoke-tests.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("references/smoke-test-checklist.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertEqual(build_manifest["generated_artifacts"]["manifest_path"], "docs/architecture/host-artifacts-manifest.json")
        self.assertEqual(build_manifest["generated_artifacts"]["artifacts"][0]["name"], "forge-codex-global-agents")
        self.assertEqual(build_manifest["generated_artifacts"]["artifacts"][0]["bundle_output"], "AGENTS.global.md")
        self.assertEqual(len(build_manifest["generated_artifacts"]["artifacts"][0]["source_sha256"]), 64)
        self.assertEqual(len(build_manifest["generated_artifacts"]["artifacts"][0]["output_sha256"]), 64)
        rendered = install_bundle_host.render_codex_global_agents(
            (dist_root / "AGENTS.global.md").read_text(encoding="utf-8"),
            dist_root.parent,
            dist_root,
        )
        self.assertNotRegex(rendered, re.compile(r"\{\{[A-Z0-9_]+\}\}"))
        self.assert_routing_locale_config(dist_root / "data" / "routing-locales.json", label="dist forge-codex")
        self.assert_output_contract_profiles(dist_root / "data" / "output-contracts.json", label="dist forge-codex")
        self.assert_codex_global_agents_bootstraps_preferences(
            dist_root / "AGENTS.global.md",
            label="dist forge-codex agents",
        )
        self.assert_session_restores_preferences(
            dist_root / "workflows" / "operator" / "session.md",
            label="dist forge-codex session",
        )

        registry = json.loads((dist_root / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        self.assertNotIn("intents", registry)
        self.assertEqual(registry["host_capabilities"]["active_tier"], "parallel-workers")
        self.assertTrue(registry["host_capabilities"]["supports_subagents"])
        self.assertEqual(
            registry["host_capabilities"]["subagent_dispatch_skill"],
            "forge-dispatching-parallel-agents",
        )
        self.assertEqual(
            registry["host_operator_surface"]["session_modes"]["restore"]["natural_language_examples_by_host"]["codex"],
            ["Continue the task we were working on yesterday and tell me the best next step."],
        )
        dist_skill = (dist_root / "SKILL.md").read_text(encoding="utf-8")
        self.assert_markdown_first_adapter_skill(
            dist_root / "SKILL.md",
            label="dist forge-codex skill",
        )
        self.assertIn("forge-verification-before-completion", dist_skill)
        self.assertIn("forge-finishing-a-development-branch", dist_skill)
        self.assertNotIn("review-pack", dist_skill)
        self.assertNotIn("release-readiness", dist_skill)
        self.assertNotIn("adoption-check", dist_skill)
        self.assertNotIn("save-brain", dist_skill)
        self.assertNotIn("/save-brain", (dist_root / "workflows" / "operator" / "session.md").read_text(encoding="utf-8"))
        dist_codex_surface = (dist_root / "references" / "codex-operator-surface.md").read_text(encoding="utf-8")
        self.assertNotIn("/delegate", dist_codex_surface)
        self.assertNotIn("/save-brain", dist_codex_surface)
        rendered_agents = (dist_root / "AGENTS.global.md").read_text(encoding="utf-8")
        self.assertNotIn("/customize", rendered_agents)
        self.assertNotIn("/init", rendered_agents)
        self.assertNotIn("Compatibility aliases:", rendered_agents)
        self.assertNotIn("Operator aliases:", rendered_agents)

        antigravity_dist_root = ROOT_DIR / "dist" / "forge-antigravity"
        self.assert_bump_wrapper_matches_release_contract(
            antigravity_dist_root / "workflows" / "operator" / "bump.md",
            label="dist forge-antigravity",
        )
        self.assert_bump_wrapper_matches_release_contract(
            dist_root / "workflows" / "operator" / "bump.md",
            label="dist forge-codex",
        )

        antigravity_registry = json.loads((antigravity_dist_root / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(antigravity_registry["host_capabilities"]["active_tier"], "controller-baseline")
        self.assertFalse(antigravity_registry["host_capabilities"]["supports_subagents"])
