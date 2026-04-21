from __future__ import annotations

import json
import re
import unittest

from support import (
    ROOT_DIR,
    bundle_package_name,
    forge_home_fixture,
    is_core_bundle,
    load_json_fixture,
    load_output_contract_profiles,
    workspace_fixture,
)


class BundleContractTests(unittest.TestCase):
    def _raw_line_count(self, path: Path) -> int:
        text = path.read_text(encoding="utf-8")
        return text.count("\n") + (0 if text.endswith("\n") else 1)

    def test_core_runtime_assets_do_not_embed_codex_assumptions(self) -> None:
        if not is_core_bundle():
            self.skipTest("Adapter bundles may add host-specific behavior on top of Forge core.")

        for relative_dir in ("scripts", "data", "workflows"):
            for path in (ROOT_DIR / relative_dir).rglob("*"):
                if not path.is_file() or path.suffix not in {".py", ".json", ".md"}:
                    continue
                text = path.read_text(encoding="utf-8").casefold()
                relative_path = path.relative_to(ROOT_DIR)
                with self.subTest(path=str(relative_path)):
                    self.assertNotIn("forge-codex", text)
                    self.assertNotIn(".codex", text)
                    self.assertNotIn("codex", text)

    def test_registry_chains_reference_known_skills(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        known_skills = {path.stem for path in (ROOT_DIR / "workflows" / "design").glob("*.md")}
        known_skills.update(path.stem for path in (ROOT_DIR / "workflows" / "execution").glob("*.md"))

        for intent, config in registry["intents"].items():
            for complexity, chain in config["chains"].items():
                with self.subTest(intent=intent, complexity=complexity):
                    self.assertTrue(set(chain).issubset(known_skills), chain)

    def test_solo_profile_stage_contract_references_known_workflows(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        known_skills = {path.stem for path in (ROOT_DIR / "workflows" / "design").glob("*.md")}
        known_skills.update(path.stem for path in (ROOT_DIR / "workflows" / "execution").glob("*.md"))
        profile_contract = registry["solo_profiles"]

        self.assertEqual(
            profile_contract["activation_reasons"],
            [
                "default_chain",
                "greenfield_feature",
                "ui_medium_plus",
                "interaction_model_change",
                "boundary_risk",
                "packet_unclear",
                "shared_env_release",
                "public_release",
                "critical_internal_release",
            ],
        )
        self.assertEqual(
            profile_contract["skip_reasons"],
            [
                "non_ui",
                "direction_locked",
                "packet_clear",
                "low_risk_boundary",
            ],
        )
        self.assertEqual(
            profile_contract["stage_statuses"],
            ["pending", "required", "active", "completed", "skipped", "blocked"],
        )
        self.assertEqual(
            set(profile_contract["stages"]),
            {
                "brainstorm",
                "plan",
                "visualize",
                "architect",
                "build",
                "test",
                "self-review",
                "secure",
                "quality-gate",
                "deploy",
                "debug",
                "refactor",
                "review",
                "session",
            },
        )

        for stage_name, stage in profile_contract["stages"].items():
            with self.subTest(stage=stage_name):
                self.assertIn(stage["workflow"], known_skills)

        for profile_name, profile in profile_contract["profiles"].items():
            for intent, order in profile["intent_orders"].items():
                with self.subTest(profile=profile_name, intent=intent):
                    self.assertTrue(order)
                    self.assertTrue(set(order).issubset(set(profile_contract["stages"])))

    def test_flat_build_registry_has_no_active_spec_review_surface(self) -> None:
        registry_text = (ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
        registry = json.loads(registry_text)

        self.assertNotIn("spec_review_gate", registry)
        self.assertNotIn("implementer-spec-quality", registry.get("execution_pipelines", {}))
        self.assertNotIn("spec-review", registry["solo_profiles"]["stages"])
        for forbidden in (
            "spec-reviewer",
            "requires_spec_review",
            "spec_review_loop_max_revisions",
        ):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden, registry_text)

    def test_spec_review_workflow_is_not_shipped_as_active_workflow(self) -> None:
        self.assertFalse((ROOT_DIR / "workflows" / "design" / "spec-review.md").exists())

    def test_brainstorm_contract_owns_flat_readiness_checkpoint(self) -> None:
        brainstorm = (ROOT_DIR / "workflows" / "design" / "brainstorm.md").read_text(encoding="utf-8")

        self.assertIn("Flat Readiness Checkpoint", brainstorm)
        self.assertIn("all behavioral build work", brainstorm)
        self.assertIn("Plan-readiness handoff", brainstorm)

    def test_canonical_registry_stays_ascii_only(self) -> None:
        registry_text = (ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
        self.assertTrue(registry_text.isascii())

    def test_skill_usage_footer_contract_is_defined(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        footer = registry["skill_usage_footer_contract"]

        self.assertEqual(footer["prefix"], "Skills used:")
        self.assertEqual(footer["none_token"], "none")
        self.assertEqual(footer["separator"], ",")
        self.assertFalse(footer["require_on_every_response"])
        self.assertTrue(footer["require_final_line"])
        self.assertTrue(footer["require_unique_skills"])
        self.assertFalse(footer["allow_none_token"])

    def test_skill_selection_explanation_contract_is_defined(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        explanation = registry["skill_selection_explanation_contract"]
        reason_labels = registry["skill_selection_reason_labels"]

        self.assertEqual(explanation["heading"], "Skill selection:")
        self.assertEqual(explanation["none_prefix"], "none -")
        self.assertEqual(explanation["bullet_prefix"], "- ")
        self.assertFalse(explanation["require_on_every_response"])
        self.assertTrue(explanation["require_at_start"])
        self.assertFalse(explanation["require_reason_text"])
        self.assertTrue(explanation["require_match_with_footer"])
        self.assertFalse(explanation["allow_in_responses"])
        self.assertIn("default_chain", reason_labels)
        self.assertIn("boundary_risk", reason_labels)

    def test_host_capability_contract_v2_defines_tiers_and_reasons(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        host = registry["host_capabilities"]
        tiers = host.get("tiers")

        self.assertEqual(host.get("contract_version"), "v2")
        self.assertIsInstance(tiers, dict)
        self.assertIn(host.get("default_tier"), tiers)
        if host.get("active_tier") is not None:
            self.assertIn(host.get("active_tier"), tiers)
        if is_core_bundle():
            self.assertNotIn("active_tier", host)
        self.assertIn("controller-baseline", tiers)
        self.assertIn("review-lane-subagents", tiers)
        self.assertIn("parallel-workers", tiers)

        for tier_name, tier in tiers.items():
            with self.subTest(tier=tier_name):
                self.assertIn(tier.get("dispatch_mode"), {"controller-sequential", "independent-reviewers", "parallel-workers"})
                self.assertIsInstance(tier.get("supports_subagents"), bool)
                self.assertIsInstance(tier.get("supports_parallel_subagents"), bool)
                self.assertIsInstance(tier.get("dispatch_reasons"), list)
                self.assertIsInstance(tier.get("fallback_reasons"), list)

    def test_bundle_locale_and_output_contract_assets_follow_bundle_boundary(self) -> None:
        routing_locale_config = ROOT_DIR / "data" / "routing-locales.json"
        routing_locale_dir = ROOT_DIR / "data" / "routing-locales"
        output_contracts_path = ROOT_DIR / "data" / "output-contracts.json"

        if is_core_bundle():
            self.assertFalse(routing_locale_config.exists())
            self.assertFalse(routing_locale_dir.exists())
            self.assertFalse(output_contracts_path.exists())
            return

        if routing_locale_config.exists():
            payload = json.loads(routing_locale_config.read_text(encoding="utf-8"))
            enabled_locales = payload.get("enabled_locales", [])
            self.assertIsInstance(enabled_locales, list)
            self.assertTrue(routing_locale_dir.exists())
            for locale_name in enabled_locales:
                with self.subTest(bundle=bundle_package_name(), locale=locale_name):
                    self.assertIsInstance(locale_name, str)
                    self.assertTrue((routing_locale_dir / f"{locale_name}.json").exists())
        else:
            self.assertFalse(routing_locale_dir.exists())

        if output_contracts_path.exists():
            profiles = load_output_contract_profiles()
            self.assertIsInstance(profiles, dict)
            self.assertTrue(
                isinstance(profiles.get("languages"), dict) or isinstance(profiles.get("orthographies"), dict)
            )

    def test_enabled_locale_assets_use_utf8_without_mojibake(self) -> None:
        routing_locale_config = ROOT_DIR / "data" / "routing-locales.json"
        routing_locale_dir = ROOT_DIR / "data" / "routing-locales"
        if not routing_locale_config.exists():
            self.skipTest("Bundle does not ship locale assets.")

        payload = json.loads(routing_locale_config.read_text(encoding="utf-8"))
        markers = ("Ã", "á»", "Ä‘", "Æ°", "â€œ", "â€", "\ufffd")
        for locale_name in payload.get("enabled_locales", []):
            locale_path = routing_locale_dir / f"{locale_name}.json"
            text = locale_path.read_text(encoding="utf-8")
            with self.subTest(bundle=bundle_package_name(), locale=locale_name):
                for marker in markers:
                    self.assertNotIn(marker, text)
                if locale_name == "vi":
                    self.assertTrue(any(char in text for char in "ăâđêôơưÁÀẢÃẠáàảãạ"))

    def test_reference_map_entries_exist(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        files = re.findall(r"\| `([^`]+)` \|", reference_map)
        for name in files:
            with self.subTest(reference=name):
                self.assertTrue((ROOT_DIR / "references" / name).exists(), name)

    def test_reference_map_points_to_current_docs_not_an_active_roadmap(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        architecture_path = ROOT_DIR.parents[1] / "docs" / "current" / "architecture.md"
        if not architecture_path.exists():
            self.skipTest("Current source-repo docs only exist in the source repository layout.")
        architecture = architecture_path.read_text(encoding="utf-8")
        target_state = (ROOT_DIR / "references" / "target-state.md").read_text(encoding="utf-8")
        self.assertIn("docs/current/architecture.md", reference_map)
        self.assertIn("maintenance-only posture", reference_map)
        self.assertNotIn("Active roadmap tranche for the current kernel-only contraction line", reference_map)
        self.assertNotIn("docs/plans/2026-04-11-forge-slim-refactor-v2.md", reference_map)
        self.assertIn("## Current maintenance posture", architecture)
        self.assertNotIn("## Active refactor focus", architecture)
        self.assertIn("## 1.16.x Surface Slim Closure", target_state)
        self.assertIn("There is no active roadmap tranche now.", target_state)
        self.assertNotIn("The active `1.16.x` surface-slim tranche", target_state)

    def test_help_next_contract_prefers_workflow_state_and_runtime_recovery_guidance(self) -> None:
        help_next = (ROOT_DIR / "references" / "help-next.md").read_text(encoding="utf-8")
        operator_recommendations = (ROOT_DIR / "scripts" / "operator_recommendations.py").read_text(encoding="utf-8")
        workflow_summary = (ROOT_DIR / "scripts" / "workflow_state_summary.py").read_text(encoding="utf-8")
        target_state = (ROOT_DIR / "references" / "target-state.md").read_text(encoding="utf-8")

        self.assertLess(
            help_next.index(".forge-artifacts/workflow-state/<project>/latest.json"),
            help_next.index("docs/plans/"),
        )
        self.assertNotIn("runtime doctor", help_next)
        self.assertNotIn("runtime doctor", operator_recommendations)
        self.assertNotIn("runtime doctor", workflow_summary)
        self.assertNotIn("doctor-style diagnostics", target_state)

    def test_fixture_manifests_resolve_real_paths(self) -> None:
        for case in load_json_fixture("route_preview_cases.json"):
            fixture_name = case.get("workspace_fixture")
            if fixture_name:
                with self.subTest(route_case=case["name"]):
                    fixture_root = workspace_fixture(fixture_name)
                    self.assertTrue(fixture_root.exists())
                    router = case.get("workspace_router")
                    if router:
                        self.assertTrue((fixture_root / router).exists())

        for case in load_json_fixture("router_check_cases.json"):
            with self.subTest(router_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())

        for case in load_json_fixture("preferences_cases.json"):
            with self.subTest(preferences_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())
                if case.get("forge_home_fixture"):
                    self.assertTrue(forge_home_fixture(case["forge_home_fixture"]).exists())

        for case in load_json_fixture("help_next_cases.json"):
            with self.subTest(help_next_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())

        for case in load_json_fixture("run_cases.json"):
            with self.subTest(run_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())

        for case in load_json_fixture("error_translation_cases.json"):
            with self.subTest(error_translation_case=case["name"]):
                self.assertTrue(bool(case["error_text"].strip()))

        for case in load_json_fixture("bump_cases.json"):
            with self.subTest(bump_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())

        for case in load_json_fixture("rollback_cases.json"):
            with self.subTest(rollback_case=case["name"]):
                self.assertIn(case["scope"], {"deploy", "config", "migration", "code-change"})

        for case in load_json_fixture("preferences_write_cases.json"):
            with self.subTest(preferences_write_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())
                if case.get("forge_home_fixture"):
                    self.assertTrue(forge_home_fixture(case["forge_home_fixture"]).exists())

        for case in load_json_fixture("workspace_init_cases.json"):
            with self.subTest(workspace_init_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())
                if case.get("forge_home_fixture"):
                    self.assertTrue(forge_home_fixture(case["forge_home_fixture"]).exists())

    def test_tooling_docs_mention_verify_entrypoints(self) -> None:
        tooling = (ROOT_DIR / "references" / "kernel-tooling.md").read_text(encoding="utf-8")
        self.assertIn("generate_requirements_checklist.py", tooling)
        self.assertIn("check_spec_packet.py", tooling)
        self.assertIn("generate_overlay_skills.py", tooling)
        self.assertIn("prepare_worktree.py", tooling)
        self.assertIn("run_smoke_matrix.py", tooling)
        self.assertIn("verify_bundle.py", tooling)
        self.assertIn("resolve_preferences.py", tooling)
        self.assertIn("resolve_help_next.py", tooling)
        self.assertIn("session_context.py", tooling)
        self.assertIn("run_with_guidance.py", tooling)
        self.assertIn("record_quality_gate.py", tooling)
        self.assertIn("translate_error.py", tooling)
        self.assertIn("prepare_bump.py", tooling)
        self.assertIn("resolve_rollback.py", tooling)
        self.assertIn("host-artifacts-manifest.json", tooling)
        self.assertIn("write_preferences.py", tooling)
        self.assertIn("initialize_workspace.py", tooling)

    def test_skill_bootstrap_contract_sections_remain_visible(self) -> None:
        skill = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
        for heading in (
            "## Bootstrap Rules",
            "## Routing Contract",
            "## Verification Contract",
            "## Solo Profile And Workflow-State Contract",
            "## Skill Laws",
            "## Reference Map",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, skill)
        for token in ("data/orchestrator-registry.json", "references/kernel-tooling.md"):
            with self.subTest(token=token):
                self.assertIn(token, skill)

    def test_shared_verification_contract_requires_red_before_implementation(self) -> None:
        skill = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("write and verify one failing test before implementation code", skill)
        self.assertIn("Code written before RED must be deleted", skill)
        self.assertIn("build`: no behavioral change with a viable harness without a failing test first", skill)

    def test_build_workflow_hard_gates_delete_rule_and_tdd_reference(self) -> None:
        build = (ROOT_DIR / "workflows" / "execution" / "build.md").read_text(encoding="utf-8")

        self.assertIn("NO BEHAVIORAL CHANGE WITHOUT A FAILING TEST FIRST", build)
        self.assertIn("Code written before a failing test: delete it and start from RED.", build)
        self.assertIn("\"Keep as reference\" is not an exception. Delete means delete.", build)
        self.assertIn("references/tdd-discipline.md", build)

    def test_tdd_discipline_reference_exists_and_captures_delete_rule(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        tdd_reference = ROOT_DIR / "references" / "tdd-discipline.md"

        self.assertIn("`tdd-discipline.md`", reference_map)
        self.assertTrue(tdd_reference.exists())

        discipline = tdd_reference.read_text(encoding="utf-8")
        self.assertIn("Delete means delete.", discipline)
        self.assertIn("RED -> GREEN -> REFACTOR", discipline)
        self.assertIn("Tests-after asks \"what does this code do?\"", discipline)

    def test_skill_bootstrap_contract_does_not_regrow_removed_lookup_sections(self) -> None:
        skill = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
        for heading in (
            "## Bundle Layout",
            "## Executable Tooling",
            "## Intent Detection",
            "## Complexity Assessment",
            "## Skill Composition Matrix",
            "## Skill Registry",
            "## Global Resilience",
            "## Golden Rules",
        ):
            with self.subTest(heading=heading):
                self.assertNotIn(heading, skill)

    def test_core_skill_line_budget_remains_thin(self) -> None:
        if not is_core_bundle():
            self.skipTest("Core line budget only applies to the core source bundle.")
        self.assertLessEqual(self._raw_line_count(ROOT_DIR / "SKILL.md"), 80)

    def test_v41_facade_line_budgets_hold(self) -> None:
        budgets = {
            "scripts/workflow_state_projection.py": 140,
            "scripts/operator_state_resolution.py": 140,
            "scripts/route_delegation.py": 180,
            "scripts/route_analysis.py": 180,
            "scripts/route_preview.py": 280,
            "scripts/workflow_state_support.py": 220,
            "scripts/help_next_support.py": 260,
        }
        for relative_path, limit in budgets.items():
            with self.subTest(path=relative_path):
                self.assertLessEqual(self._raw_line_count(ROOT_DIR / relative_path), limit)

    def test_session_workflow_mentions_preferences_restore_contract(self) -> None:
        session = (ROOT_DIR / "workflows" / "execution" / "session.md").read_text(encoding="utf-8")

        self.assertIn("adapter-global", session)
        self.assertIn("state/preferences.json", session)
        self.assertNotIn("state/extra_preferences.json", session)
        self.assertIn("resolve_preferences.py", session)
        self.assertIn("session_context.py", session)
        self.assertIn("save context", session)
        self.assertIn("resume", session)
        self.assertIn("Response Personalization", session)
        self.assertIn("workflow-state", session)

    def test_preferences_surface_uses_legacy_extra_helper_names_only(self) -> None:
        common_text = (ROOT_DIR / "scripts" / "common.py").read_text(encoding="utf-8")
        preferences_text = (ROOT_DIR / "scripts" / "preferences.py").read_text(encoding="utf-8")

        for text in (common_text, preferences_text):
            self.assertRegex(text, r"\bLEGACY_GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH\b")
            self.assertRegex(text, r"\bresolve_legacy_global_extra_preferences_path\b")
            self.assertRegex(text, r"\bresolve_legacy_installed_extra_preferences_path\b")
            self.assertNotRegex(text, r"\bGLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH\b")
            self.assertNotRegex(text, r"\bresolve_global_extra_preferences_path\b")
            self.assertNotRegex(text, r"\bresolve_installed_extra_preferences_path\b")

    def test_operator_surface_registry_metadata_is_complete(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        required_fields = {
            "repo_entrypoint",
            "core_engine_entrypoint",
            "workflow",
            "hosts",
            "primary_aliases_by_host",
            "compatibility_aliases_by_host",
            "natural_language_examples_by_host",
            "deprecation_line",
            "status",
        }

        self.assertNotIn("operator_surface", registry)

        expected_non_empty = {
            "repo_operator_surface": {"actions"},
            "host_operator_surface": {"actions", "session_modes"},
        }

        for surface_name, non_empty_sections in expected_non_empty.items():
            surface = registry[surface_name]
            for section_name in ("actions", "session_modes"):
                section = surface[section_name]
                self.assertIsInstance(section, dict)
                if section_name in non_empty_sections:
                    self.assertTrue(section)
                for item_name, metadata in section.items():
                    with self.subTest(surface=surface_name, section=section_name, item=item_name):
                        self.assertTrue(required_fields.issubset(metadata))
                        self.assertIn(metadata["status"], {"primary", "compat"})
                        self.assertIsInstance(metadata["hosts"], list)
                        self.assertIsInstance(metadata["primary_aliases_by_host"], dict)
                        self.assertIsInstance(metadata["compatibility_aliases_by_host"], dict)
                        self.assertIsInstance(metadata["natural_language_examples_by_host"], dict)
                        if metadata["status"] == "compat":
                            self.assertTrue(metadata["deprecation_line"])

    def test_operator_surface_workflow_paths_stay_bounded(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))

        for surface_name in ("repo_operator_surface", "host_operator_surface"):
            surface = registry[surface_name]
            for section_name in ("actions", "session_modes"):
                for item_name, metadata in surface[section_name].items():
                    workflow = metadata["workflow"]
                    with self.subTest(surface=surface_name, section=section_name, item=item_name):
                        self.assertTrue(workflow.startswith("workflows/"))
                        self.assertTrue((ROOT_DIR / workflow).exists(), workflow)

    def test_release_bundle_matrix_stays_kernel_only(self) -> None:
        repo_root = ROOT_DIR.parents[1]
        package_matrix_path = repo_root / "docs" / "release" / "package-matrix.json"
        if not package_matrix_path.exists():
            self.skipTest("Release package matrix only exists in the source repository layout.")
        package_matrix = json.loads(package_matrix_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [bundle["name"] for bundle in package_matrix["bundles"]],
            ["forge-core", "forge-antigravity", "forge-codex"],
        )

    def test_tooling_docs_mention_workflow_state_artifacts(self) -> None:
        tooling = (ROOT_DIR / "references" / "kernel-tooling.md").read_text(encoding="utf-8")
        self.assertIn("workflow-state", tooling)
        self.assertIn("latest.json", tooling)
        self.assertIn("events.jsonl", tooling)

    def test_reference_map_mentions_artifact_driven_change_flow(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        self.assertIn("constitution-lite.md", reference_map)
        self.assertIn("target-state.md", reference_map)
        self.assertIn("extension-presets.md", reference_map)

    def test_extension_preset_boundary_docs_and_example_artifact_exist(self) -> None:
        extension_presets = (ROOT_DIR / "references" / "extension-presets.md").read_text(encoding="utf-8")
        architecture_layers = (ROOT_DIR / "references" / "architecture-layers.md").read_text(encoding="utf-8")
        example_path = ROOT_DIR / "references" / "examples" / "example-fast-lane-packet.json"
        example = json.loads(example_path.read_text(encoding="utf-8"))

        self.assertIn("packet templates", extension_presets)
        self.assertIn("workflow overlays", extension_presets)
        self.assertIn("planning presets", extension_presets)
        self.assertIn("cannot override core verification", extension_presets)
        self.assertIn("Bounded Extension Surface (1.14.x)", architecture_layers)
        self.assertEqual(example["packet"]["packet_mode"], "fast-lane")
        self.assertIn("boundary_note", example)

    def test_help_next_reference_mentions_unscoped_stage_and_current_stage(self) -> None:
        help_next = (ROOT_DIR / "references" / "help-next.md").read_text(encoding="utf-8")
        self.assertIn("`unscoped`", help_next)
        self.assertIn("`current_stage`", help_next)
        self.assertIn("target-state.md", help_next)

    def test_help_and_next_workflows_reference_target_state_for_forge_maintenance(self) -> None:
        help_workflow = (ROOT_DIR / "workflows" / "operator" / "help.md").read_text(encoding="utf-8")
        next_workflow = (ROOT_DIR / "workflows" / "operator" / "next.md").read_text(encoding="utf-8")
        self.assertIn("references/target-state.md", help_workflow)
        self.assertIn("references/target-state.md", next_workflow)

    def test_run_guidance_reference_mentions_error_translation(self) -> None:
        run_guidance = (ROOT_DIR / "references" / "run-guidance.md").read_text(encoding="utf-8")
        run_workflow = (ROOT_DIR / "workflows" / "operator" / "run.md").read_text(encoding="utf-8")
        self.assertIn("error_translation", run_guidance)
        self.assertIn("Error translation:", run_workflow)

    def test_architecture_layers_reference_describes_three_layers(self) -> None:
        architecture = (ROOT_DIR / "references" / "architecture-layers.md").read_text(encoding="utf-8")
        self.assertIn("core", architecture)
        self.assertIn("generated artifacts", architecture)
        self.assertIn("workflow state", architecture)
        self.assertIn("generate_host_artifacts.py", architecture)

    def test_architecture_layers_reference_mentions_three_layers(self) -> None:
        layers = (ROOT_DIR / "references" / "architecture-layers.md").read_text(encoding="utf-8")
        self.assertIn("core", layers)
        self.assertIn("generated artifacts", layers)
        self.assertIn("workflow state", layers)
        self.assertIn("Dependency Direction", layers)
        self.assertIn("packet-index.json", layers)


if __name__ == "__main__":
    unittest.main()
