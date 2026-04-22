from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_REPO_SCRIPTS_DIR = ROOT_DIR.parents[2] / "scripts"


def resolve_core_root() -> Path:
    if (ROOT_DIR / "scripts").exists() and (ROOT_DIR / "data").exists():
        return ROOT_DIR
    return ROOT_DIR.parents[1] / "forge-core"


CORE_ROOT_DIR = resolve_core_root()
CORE_SCRIPTS_DIR = CORE_ROOT_DIR / "scripts"


def merge_overlay(base: object, overlay: object) -> object:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in overlay.items():
            merged[key] = merge_overlay(merged[key], value) if key in merged else copy.deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(overlay, list):
        merged = [copy.deepcopy(item) for item in base]
        seen = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in merged}
        for item in overlay:
            marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if marker not in seen:
                seen.add(marker)
                merged.append(copy.deepcopy(item))
        return merged
    return copy.deepcopy(overlay)


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stage_bundle_root() -> Path:
    stage_root = Path(tempfile.mkdtemp(prefix="forge-antigravity-bundle-"))
    stage_data_dir = stage_root / "data"
    shutil.copytree(CORE_ROOT_DIR / "data", stage_data_dir, dirs_exist_ok=True)
    write_json(
        stage_data_dir / "orchestrator-registry.json",
        merge_overlay(
            load_json(CORE_ROOT_DIR / "data" / "orchestrator-registry.json"),
            load_json(ROOT_DIR / "data" / "orchestrator-registry.json"),
        ),
    )
    for filename in ("output-contracts.json", "routing-locales.json"):
        source = ROOT_DIR / "data" / filename
        if source.exists():
            shutil.copy2(source, stage_data_dir / filename)
    locale_dir = ROOT_DIR / "data" / "routing-locales"
    if locale_dir.exists():
        shutil.copytree(locale_dir, stage_data_dir / "routing-locales", dirs_exist_ok=True)
    skill_source = ROOT_DIR / "SKILL.md"
    if skill_source.exists():
        shutil.copy2(skill_source, stage_root / "SKILL.md")
    return stage_root


os.environ["FORGE_BUNDLE_ROOT"] = str(stage_bundle_root())

if str(CORE_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_SCRIPTS_DIR))
if str(SOURCE_REPO_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_REPO_SCRIPTS_DIR))

for module_name in ("common", "preferences", "preferences_contract", "preferences_paths", "response_contract", "skill_routing"):
    sys.modules.pop(module_name, None)

import common  # noqa: E402
import response_contract  # noqa: E402
import skill_routing  # noqa: E402


def load_output_contract_profiles() -> dict | None:
    if not common.OUTPUT_CONTRACTS_PATH.exists():
        return None
    payload = json.loads(common.OUTPUT_CONTRACTS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def expected_output_contract(extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return {}
    contract: dict[str, object] = {}
    profiles = load_output_contract_profiles()
    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = common.normalize_choice_token(language)
        contract["language"] = normalized_language
        languages = profiles.get("languages") if isinstance(profiles, dict) else None
        profile = languages.get(normalized_language) if isinstance(languages, dict) else None
        if isinstance(profile, dict):
            profile_contract = profile.get("contract")
            if isinstance(profile_contract, dict):
                contract.update(copy.deepcopy(profile_contract))
            default_orthography = profile.get("default_orthography")
            if isinstance(default_orthography, str) and "orthography" not in contract:
                normalized = common.normalize_choice_token(default_orthography)
                contract["orthography"] = normalized
                orthographies = profiles.get("orthographies") if isinstance(profiles, dict) else None
                orthography_profile = orthographies.get(normalized) if isinstance(orthographies, dict) else None
                if isinstance(orthography_profile, dict):
                    contract.update(copy.deepcopy(orthography_profile))
    return contract


class AdapterLocaleTests(unittest.TestCase):
    def test_overlay_skill_bootstrap_uses_markdown_first_contract(self) -> None:
        skill = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8").casefold()

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
