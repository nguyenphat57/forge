from __future__ import annotations

import json
import re

from release_repo_test_support import ROOT_DIR, ReleaseRepoTestSupport
from overlay_route_fixtures import route_preview_cases_for_bundle
import build_release  # noqa: E402
import install_bundle_host  # noqa: E402


class ReleaseRepoOverlayTests(ReleaseRepoTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        build_release.build_all()

    def test_overlay_registries_inherit_core_delegation_and_release_stage_contract(self) -> None:
        core_registry = json.loads(
            (ROOT_DIR / "packages" / "forge-core" / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
        )
        delegation_contract = core_registry["host_capabilities"]["delegation_contract"]
        solo_profile_contract = core_registry["solo_profiles"]

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
            self.assertNotIn("delegation_contract", overlay_registry.get("host_capabilities", {}))
            self.assertNotIn("solo_profiles", overlay_registry)

        for bundle_name in ("forge-antigravity", "forge-codex"):
            with self.subTest(bundle=bundle_name):
                dist_registry = json.loads(
                    (ROOT_DIR / "dist" / bundle_name / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
                )
                self.assertEqual(dist_registry["host_capabilities"]["delegation_contract"], delegation_contract)
                self.assertEqual(dist_registry["solo_profiles"], solo_profile_contract)

    def test_antigravity_route_preview_fixture_is_generated_from_core_contract(self) -> None:
        core_fixture = json.loads(
            (
                ROOT_DIR
                / "packages"
                / "forge-core"
                / "tests"
                / "fixtures"
                / "route_preview_cases.json"
            ).read_text(encoding="utf-8")
        )
        overlay_fixture = route_preview_cases_for_bundle("forge-antigravity")
        self.assertIsNotNone(overlay_fixture)
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

        normalized_core_fixture = []
        for case in core_fixture:
            normalized_case = dict(case)
            normalized_case.pop("expected_host_skills", None)
            normalized_case.pop("expected_host_skills_when_subagents", None)
            normalized_core_fixture.append(normalized_case)

        self.assertEqual(overlay_fixture, normalized_core_fixture)

    def test_antigravity_wave_b_overlay_files_exist(self) -> None:
        overlay_root = ROOT_DIR / "packages" / "forge-antigravity" / "overlay"
        expected_files = [
            overlay_root / "GEMINI.global.md",
            overlay_root / "SKILL.md",
            overlay_root / "agents" / "openai.yaml",
            overlay_root / "data" / "orchestrator-registry.json",
            overlay_root / "workflows" / "operator" / "customize.md",
            overlay_root / "workflows" / "operator" / "init.md",
            overlay_root / "workflows" / "operator" / "recap.md",
            overlay_root / "workflows" / "operator" / "save-brain.md",
            overlay_root / "workflows" / "operator" / "handover.md",
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
        self.assertIn("/customize", skill)
        self.assertIn("/init", skill)
        self.assertIn("/save-brain", skill)
        self.assertIn("Solo Profile And Workflow-State Contract", skill)
        self.assertIn("review-pack", skill)
        self.assertIn("release-readiness", skill)
        self.assertIn("adoption-check", skill)
        self.assertIn("There is no `/gate` alias", skill)
        self.assert_antigravity_skill_bootstraps_preferences(
            overlay_root / "SKILL.md",
            label="forge-antigravity overlay skill",
        )
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
        self.assertIn("There is no `/gate` alias", gemini_text)
        self.assertIn("Compatibility aliases:", gemini_text)
        primary_alias_section = gemini_text.split("Primary operator aliases:", maxsplit=1)[1].split("Compatibility aliases:", maxsplit=1)[0]
        self.assertNotIn("/recap", primary_alias_section)
        self.assertNotIn("/save-brain", primary_alias_section)
        self.assertIn("/recap", gemini_text.split("Compatibility aliases:", maxsplit=1)[1])

    def test_materialized_antigravity_wave_b_overlay_contract(self) -> None:
        dist_root = ROOT_DIR / "dist" / "forge-antigravity"
        self.assertTrue((dist_root / "GEMINI.global.md").exists())
        self.assertTrue((dist_root / "SKILL.md").exists())
        self.assertTrue((dist_root / "agents" / "openai.yaml").exists())
        self.assertTrue((dist_root / "data" / "orchestrator-registry.json").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "help.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "next.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "run.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "rollback.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "customize.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "init.md").exists())
        self.assertTrue((dist_root / "workflows" / "operator" / "recap.md").exists())
        self.assertTrue((dist_root / "references" / "antigravity-operator-surface.md").exists())
        self.assertTrue((dist_root / "data" / "preferences-compat.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales" / "vi.json").exists())
        self.assertTrue((dist_root / "data" / "output-contracts.json").exists())
        self.assertTrue((dist_root / "tests" / "fixtures" / "route_preview_cases.json").exists())
        self.assertIn("GENERATED FILE", (dist_root / "GEMINI.global.md").read_text(encoding="utf-8"))
        generated_fixture = json.loads((dist_root / "tests" / "fixtures" / "route_preview_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(generated_fixture, route_preview_cases_for_bundle("forge-antigravity"))
        build_manifest = json.loads((dist_root / "BUILD-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(build_manifest["state"]["dev_root"]["env_var"], "GEMINI_HOME")
        self.assertEqual(build_manifest["state"]["dev_root"]["path_relative"], "forge-antigravity")
        self.assertEqual(build_manifest["packaging"]["default_target_strategy"], "gemini_home_skill")
        self.assertIn("GEMINI.global.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("SKILL.md", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("agents/openai.yaml", build_manifest["packaging"]["required_bundle_paths"])
        self.assertIn("tests/fixtures/route_preview_cases.json", build_manifest["packaging"]["required_bundle_paths"])
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
        self.assertIn("Compatibility aliases:", rendered_gemini)
        self.assertIn("one stable line", rendered_gemini)
        self.assert_routing_locale_config(dist_root / "data" / "routing-locales.json", label="dist forge-antigravity")
        self.assert_output_contract_profiles(dist_root / "data" / "output-contracts.json", label="dist forge-antigravity")
        self.assert_session_restores_preferences(
            dist_root / "workflows" / "execution" / "session.md",
            label="dist forge-antigravity session",
        )

    def test_codex_wave_c_overlay_files_exist(self) -> None:
        overlay_root = ROOT_DIR / "packages" / "forge-codex" / "overlay"
        expected_files = [
            overlay_root / "AGENTS.global.md",
            overlay_root / "SKILL.md",
            overlay_root / "data" / "orchestrator-registry.json",
            overlay_root / "data" / "routing-locales.json",
            overlay_root / "data" / "routing-locales" / "vi.json",
            overlay_root / "data" / "output-contracts.json",
            overlay_root / "references" / "smoke-tests.md",
            overlay_root / "references" / "smoke-test-checklist.md",
            overlay_root / "workflows" / "execution" / "dispatch-subagents.md",
            overlay_root / "workflows" / "execution" / "session.md",
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
        self.assertIn("natural-language first", skill)
        self.assertIn("dispatch-subagents", skill)
        self.assertIn("workflows/operator/customize.md", skill)
        self.assertIn("workflows/operator/init.md", skill)
        self.assertIn("AGENTS.global.md", skill)
        self.assertIn("At the start of each new thread, resolve preferences", skill)
        self.assertIn("Solo Profile And Workflow-State Contract", skill)
        self.assertIn("review-pack", skill)
        self.assertIn("release-readiness", skill)
        self.assertIn("adoption-check", skill)
        self.assertIn("There is no `/gate` alias", skill)
        self.assertNotIn("save-brain", skill)
        self.assert_codex_global_agents_bootstraps_preferences(
            overlay_root / "AGENTS.global.md",
            label="forge-codex overlay agents",
        )
        self.assertIn("GENERATED FILE", (overlay_root / "AGENTS.global.md").read_text(encoding="utf-8"))
        self.assertNotIn("/save-brain", (overlay_root / "workflows" / "execution" / "session.md").read_text(encoding="utf-8"))
        codex_surface = (overlay_root / "references" / "codex-operator-surface.md").read_text(encoding="utf-8")
        self.assertIn("/delegate", codex_surface)
        self.assertNotIn("/save-brain", codex_surface)
        self.assert_session_restores_preferences(
            overlay_root / "workflows" / "execution" / "session.md",
            label="forge-codex overlay session",
        )

    def test_materialized_codex_wave_c_overlay_contract(self) -> None:
        dist_root = ROOT_DIR / "dist" / "forge-codex"
        self.assertTrue((dist_root / "AGENTS.global.md").exists())
        self.assertTrue((dist_root / "SKILL.md").exists())
        self.assertTrue((dist_root / "data" / "orchestrator-registry.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales.json").exists())
        self.assertTrue((dist_root / "data" / "routing-locales" / "vi.json").exists())
        self.assertTrue((dist_root / "data" / "output-contracts.json").exists())
        self.assertTrue((dist_root / "references" / "smoke-tests.md").exists())
        self.assertTrue((dist_root / "references" / "smoke-test-checklist.md").exists())
        self.assertTrue((dist_root / "workflows" / "execution" / "dispatch-subagents.md").exists())
        self.assertTrue((dist_root / "workflows" / "execution" / "session.md").exists())
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
            dist_root / "workflows" / "execution" / "session.md",
            label="dist forge-codex session",
        )

        registry = json.loads((dist_root / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["intents"]["SESSION"]["shortcuts"], [])
        self.assertEqual(registry["host_capabilities"]["active_tier"], "parallel-workers")
        self.assertTrue(registry["host_capabilities"]["supports_subagents"])
        self.assertEqual(registry["host_capabilities"]["subagent_dispatch_skill"], "dispatch-subagents")
        dist_skill = (dist_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("At the start of each new thread, resolve preferences", dist_skill)
        self.assertIn("Solo Profile And Workflow-State Contract", dist_skill)
        self.assertIn("review-pack", dist_skill)
        self.assertIn("release-readiness", dist_skill)
        self.assertIn("adoption-check", dist_skill)
        self.assertIn("There is no `/gate` alias", dist_skill)
        self.assertNotIn("save-brain", dist_skill)
        self.assertNotIn("/save-brain", (dist_root / "workflows" / "execution" / "session.md").read_text(encoding="utf-8"))
        dist_codex_surface = (dist_root / "references" / "codex-operator-surface.md").read_text(encoding="utf-8")
        self.assertIn("/delegate", dist_codex_surface)
        self.assertNotIn("/save-brain", dist_codex_surface)

        antigravity_dist_root = ROOT_DIR / "dist" / "forge-antigravity"
        self.assert_bump_wrapper_matches_release_contract(
            antigravity_dist_root / "workflows" / "operator" / "bump.md",
            label="dist forge-antigravity",
        )
        self.assert_bump_wrapper_matches_release_contract(
            dist_root / "workflows" / "operator" / "bump.md",
            label="dist forge-codex",
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            (antigravity_dist_root / "SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION",
            (dist_root / "SKILL.md").read_text(encoding="utf-8"),
        )

        antigravity_registry = json.loads((antigravity_dist_root / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(antigravity_registry["host_capabilities"]["active_tier"], "controller-baseline")
        self.assertFalse(antigravity_registry["host_capabilities"]["supports_subagents"])
