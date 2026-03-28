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
    def test_core_runtime_assets_do_not_embed_codex_assumptions(self) -> None:
        if not is_core_bundle():
            self.skipTest("Adapter bundles may add host-specific behavior on top of Forge core.")

        for relative_dir in ("scripts", "data", "workflows", "domains"):
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
        known_skills = {path.stem for path in (ROOT_DIR / "domains").glob("*.md")}
        known_skills.update(path.stem for path in (ROOT_DIR / "workflows" / "design").glob("*.md"))
        known_skills.update(path.stem for path in (ROOT_DIR / "workflows" / "execution").glob("*.md"))

        for intent, config in registry["intents"].items():
            for complexity, chain in config["chains"].items():
                with self.subTest(intent=intent, complexity=complexity):
                    self.assertTrue(set(chain).issubset(known_skills), chain)

    def test_canonical_registry_stays_ascii_only(self) -> None:
        registry_text = (ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8")
        self.assertTrue(registry_text.isascii())

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
        tooling = (ROOT_DIR / "references" / "tooling.md").read_text(encoding="utf-8")
        self.assertIn("run_smoke_matrix.py", tooling)
        self.assertIn("verify_bundle.py", tooling)
        self.assertIn("record_canary_result.py", tooling)
        self.assertIn("evaluate_canary_readiness.py", tooling)
        self.assertIn("resolve_preferences.py", tooling)
        self.assertIn("resolve_help_next.py", tooling)
        self.assertIn("run_with_guidance.py", tooling)
        self.assertIn("record_quality_gate.py", tooling)
        self.assertIn("translate_error.py", tooling)
        self.assertIn("prepare_bump.py", tooling)
        self.assertIn("resolve_rollback.py", tooling)
        self.assertIn("resolve_runtime_tool.py", tooling)
        self.assertIn("invoke_runtime_tool.py", tooling)
        self.assertIn("write_preferences.py", tooling)
        self.assertIn("initialize_workspace.py", tooling)

    def test_session_workflow_mentions_preferences_restore_contract(self) -> None:
        session = (ROOT_DIR / "workflows" / "execution" / "session.md").read_text(encoding="utf-8")

        self.assertIn("adapter-global", session)
        self.assertIn("state/preferences.json", session)
        self.assertIn("state/extra_preferences.json", session)
        self.assertIn("resolve_preferences.py", session)
        self.assertIn("Response Personalization", session)
        self.assertIn("workflow-state", session)

    def test_tooling_docs_mention_workflow_state_artifacts(self) -> None:
        tooling = (ROOT_DIR / "references" / "tooling.md").read_text(encoding="utf-8")
        self.assertIn("workflow-state", tooling)
        self.assertIn("latest.json", tooling)
        self.assertIn("events.jsonl", tooling)

    def test_architecture_layers_reference_describes_four_layers(self) -> None:
        architecture = (ROOT_DIR / "references" / "architecture-layers.md").read_text(encoding="utf-8")
        self.assertIn("core", architecture)
        self.assertIn("generated artifacts", architecture)
        self.assertIn("workflow state", architecture)
        self.assertIn("runtime tools", architecture)
        self.assertIn("generate_host_artifacts.py", architecture)

    def test_architecture_layers_reference_mentions_four_layers(self) -> None:
        layers = (ROOT_DIR / "references" / "architecture-layers.md").read_text(encoding="utf-8")
        self.assertIn("core", layers)
        self.assertIn("generated artifacts", layers)
        self.assertIn("workflow state", layers)
        self.assertIn("runtime tools", layers)
        self.assertIn("Dependency Direction", layers)


if __name__ == "__main__":
    unittest.main()
