from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from support import ROOT_DIR, load_json_fixture, workspace_fixture


class BundleContractTests(unittest.TestCase):
    def test_registry_chains_reference_known_skills(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        known_skills = {path.stem for path in (ROOT_DIR / "domains").glob("*.md")}
        known_skills.update(path.stem for path in (ROOT_DIR / "workflows" / "design").glob("*.md"))
        known_skills.update(path.stem for path in (ROOT_DIR / "workflows" / "execution").glob("*.md"))

        for intent, config in registry["intents"].items():
            for complexity, chain in config["chains"].items():
                with self.subTest(intent=intent, complexity=complexity):
                    self.assertTrue(set(chain).issubset(known_skills), chain)

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

        for case in load_json_fixture("workspace_init_cases.json"):
            with self.subTest(workspace_init_case=case["name"]):
                self.assertTrue(workspace_fixture(case["workspace_fixture"]).exists())

    def test_tooling_docs_mention_verify_entrypoints(self) -> None:
        tooling = (ROOT_DIR / "references" / "tooling.md").read_text(encoding="utf-8")
        self.assertIn("run_smoke_matrix.py", tooling)
        self.assertIn("verify_bundle.py", tooling)
        self.assertIn("record_canary_result.py", tooling)
        self.assertIn("evaluate_canary_readiness.py", tooling)
        self.assertIn("resolve_preferences.py", tooling)
        self.assertIn("resolve_help_next.py", tooling)
        self.assertIn("run_with_guidance.py", tooling)
        self.assertIn("translate_error.py", tooling)
        self.assertIn("prepare_bump.py", tooling)
        self.assertIn("resolve_rollback.py", tooling)
        self.assertIn("write_preferences.py", tooling)
        self.assertIn("initialize_workspace.py", tooling)

    def test_session_workflow_mentions_preferences_restore_contract(self) -> None:
        session = (ROOT_DIR / "workflows" / "execution" / "session.md").read_text(encoding="utf-8")

        self.assertIn(".brain/preferences.json", session)
        self.assertIn("resolve_preferences.py", session)
        self.assertIn("Response Personalization", session)


if __name__ == "__main__":
    unittest.main()
