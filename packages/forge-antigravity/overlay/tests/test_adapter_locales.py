from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT_DIR / "tools"

if str(TOOLS_DIR) not in sys.path:
    sys.path.append(str(TOOLS_DIR))

SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "forge_antigravity_overlay_support",
    TOOLS_DIR / "support.py",
)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise RuntimeError("Unable to load forge-antigravity overlay support module.")
SUPPORT_MODULE = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(SUPPORT_MODULE)

STAGED_BUNDLE_ROOT = SUPPORT_MODULE.STAGED_BUNDLE_ROOT
expected_output_contract = SUPPORT_MODULE.expected_output_contract

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

    def test_host_capabilities_reflect_antigravity_sequential_support(self) -> None:
        registry = skill_routing.load_registry()
        host = registry["host_capabilities"]

        self.assertEqual(host["active_tier"], "controller-baseline")
        self.assertFalse(host["supports_subagents"])
        self.assertFalse(host["supports_parallel_subagents"])
        self.assertIsNone(host["subagent_dispatch_skill"])

    def test_host_operator_surface_preserves_natural_language_session_modes(self) -> None:
        registry = skill_routing.load_registry()
        session_modes = registry["host_operator_surface"]["session_modes"]

        self.assertEqual(session_modes["restore"]["hosts"], ["antigravity"])
        self.assertIn("Continue the task", session_modes["restore"]["natural_language_examples_by_host"]["antigravity"][0])
        self.assertEqual(session_modes["save"]["hosts"], ["antigravity"])
        self.assertEqual(session_modes["handover"]["hosts"], ["antigravity"])


if __name__ == "__main__":
    unittest.main()
