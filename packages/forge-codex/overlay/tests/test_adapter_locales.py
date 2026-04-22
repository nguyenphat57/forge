from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "forge_codex_overlay_support",
    SCRIPTS_DIR / "support.py",
)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("Unable to load forge-codex overlay support module.")
SUPPORT_MODULE = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT_MODULE)

expected_output_contract = SUPPORT_MODULE.expected_output_contract
STAGED_BUNDLE_ROOT = SUPPORT_MODULE.STAGED_BUNDLE_ROOT

import common  # noqa: E402
import response_contract  # noqa: E402
import skill_routing  # noqa: E402


class AdapterLocaleTests(unittest.TestCase):
    def test_staged_skill_bootstrap_uses_markdown_first_contract(self) -> None:
        skill = (STAGED_BUNDLE_ROOT / "SKILL.md").read_text(encoding="utf-8").casefold()

        self.assertIn("<extremely-important>", skill)
        self.assertIn("</extremely-important>", skill)
        self.assertIn("1% chance", skill)
        self.assertIn("before any response or action", skill)
        self.assertIn("workflow-first", skill)
        self.assertIn("route_preview is not the current public contract", skill)

    def test_raw_overlay_registry_keeps_only_host_contract_metadata(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))

        self.assertNotIn("intents", registry)
        self.assertNotIn("session_modes", registry)
        self.assertIn("host_operator_surface", registry)
        self.assertIn("host_capabilities", registry)

    def test_bundle_language_profiles_expand_vietnamese_output_contract(self) -> None:
        contract = common.resolve_output_contract({"language": "vi"})

        self.assertEqual(contract, expected_output_contract({"language": "vi"}))
        self.assertEqual(contract["language"], "vi")
        self.assertEqual(contract["orthography"], "vietnamese-diacritics")
        self.assertEqual(contract["accent_policy"], "required")
        self.assertEqual(contract["encoding"], "utf-8")

    def test_vietnamese_response_contract_rejects_accent_stripped_output(self) -> None:
        contract = common.resolve_output_contract({"language": "vi"})
        report = response_contract.validate_response_contract(
            "Em da xac minh: pytest -q pass. Dung vi da co evidence. Da sua: bo sung validator.",
            output_contract=contract,
            require_evidence_response=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("accent-stripped Vietnamese" in finding for finding in report["findings"]))

    def test_host_capabilities_reflect_codex_parallel_worker_support(self) -> None:
        registry = skill_routing.load_registry()
        host = registry["host_capabilities"]

        self.assertEqual(host["active_tier"], "parallel-workers")
        self.assertTrue(host["supports_subagents"])
        self.assertTrue(host["supports_parallel_subagents"])
        self.assertEqual(host["subagent_dispatch_skill"], "forge-dispatching-parallel-agents")

    def test_host_operator_surface_keeps_delegate_action_without_aliases(self) -> None:
        registry = skill_routing.load_registry()
        delegate = registry["host_operator_surface"]["actions"]["delegate"]

        self.assertEqual(delegate["workflow"], "workflows/execution/dispatch-subagents.md")
        self.assertEqual(delegate["primary_aliases_by_host"], {})
        self.assertEqual(delegate["hosts"], ["codex"])


if __name__ == "__main__":
    unittest.main()
