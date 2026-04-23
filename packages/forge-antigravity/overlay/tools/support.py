from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_REPO_SCRIPTS_DIR = ROOT_DIR.parents[2] / "scripts"


def resolve_core_root_dir() -> Path:
    materialized_bundle = ROOT_DIR / "BUILD-MANIFEST.json"
    if materialized_bundle.exists():
        return ROOT_DIR

    source_core_root = ROOT_DIR.parents[1] / "forge-core"
    if source_core_root.exists():
        return source_core_root

    return ROOT_DIR


CORE_ROOT_DIR = resolve_core_root_dir()
CORE_SHARED_DIR = CORE_ROOT_DIR / "shared"


def merge_overlay(base: object, overlay: object) -> object:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in overlay.items():
            if key in merged:
                merged[key] = merge_overlay(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged

    if isinstance(base, list) and isinstance(overlay, list):
        merged = [copy.deepcopy(item) for item in base]
        seen = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in merged}
        for item in overlay:
            marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if marker in seen:
                continue
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
    if CORE_ROOT_DIR == ROOT_DIR:
        return ROOT_DIR

    if str(SOURCE_REPO_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCE_REPO_SCRIPTS_DIR))

    from skill_bundle_composer import write_composed_adapter_skill  # noqa: E402

    stage_root = Path(tempfile.mkdtemp(prefix="forge-antigravity-bundle-"))
    stage_data_dir = stage_root / "data"
    core_data_dir = CORE_ROOT_DIR / "data"
    overlay_data_dir = ROOT_DIR / "data"

    shutil.copytree(core_data_dir, stage_data_dir, dirs_exist_ok=True)
    write_composed_adapter_skill("forge-antigravity", stage_root / "SKILL.md")

    core_registry = load_json(core_data_dir / "orchestrator-registry.json")
    overlay_registry = load_json(overlay_data_dir / "orchestrator-registry.json")
    write_json(stage_data_dir / "orchestrator-registry.json", merge_overlay(core_registry, overlay_registry))

    core_output_contracts_path = core_data_dir / "output-contracts.json"
    overlay_output_contracts_path = overlay_data_dir / "output-contracts.json"
    if core_output_contracts_path.exists() or overlay_output_contracts_path.exists():
        base_output_contracts = load_json(core_output_contracts_path) if core_output_contracts_path.exists() else {}
        overlay_output_contracts = (
            load_json(overlay_output_contracts_path) if overlay_output_contracts_path.exists() else {}
        )
        write_json(stage_data_dir / "output-contracts.json", merge_overlay(base_output_contracts, overlay_output_contracts))

    routing_locale_config_path = overlay_data_dir / "routing-locales.json"
    if routing_locale_config_path.exists():
        shutil.copy2(routing_locale_config_path, stage_data_dir / "routing-locales.json")
    routing_locale_dir = overlay_data_dir / "routing-locales"
    if routing_locale_dir.exists():
        shutil.copytree(routing_locale_dir, stage_data_dir / "routing-locales", dirs_exist_ok=True)

    return stage_root


STAGED_BUNDLE_ROOT = stage_bundle_root()

os.environ["FORGE_BUNDLE_ROOT"] = str(STAGED_BUNDLE_ROOT)

if str(CORE_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_SHARED_DIR))

for module_name in (
    "common",
    "preferences",
    "preferences_contract",
    "preferences_paths",
    "response_contract",
    "skill_routing",
):
    sys.modules.pop(module_name, None)

import common  # noqa: E402


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
    language_profile: dict[str, object] | None = None

    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = common.normalize_choice_token(language)
        contract["language"] = normalized_language
        if isinstance(profiles, dict):
            languages = profiles.get("languages")
            if isinstance(languages, dict):
                profile = languages.get(normalized_language)
                if isinstance(profile, dict):
                    language_profile = profile
                    profile_contract = profile.get("contract")
                    if isinstance(profile_contract, dict):
                        contract.update(copy.deepcopy(profile_contract))

    orthography = extra.get("orthography")
    if isinstance(orthography, str) and orthography.strip():
        normalized_orthography = common.normalize_choice_token(orthography)
        contract["orthography"] = normalized_orthography
        if isinstance(profiles, dict):
            orthographies = profiles.get("orthographies")
            if isinstance(orthographies, dict):
                profile = orthographies.get(normalized_orthography)
                if isinstance(profile, dict):
                    contract.update(copy.deepcopy(profile))

    if "orthography" not in contract and isinstance(language_profile, dict):
        default_orthography = language_profile.get("default_orthography")
        if isinstance(default_orthography, str) and default_orthography.strip():
            normalized_orthography = common.normalize_choice_token(default_orthography)
            contract["orthography"] = normalized_orthography
            if isinstance(profiles, dict):
                orthographies = profiles.get("orthographies")
                if isinstance(orthographies, dict):
                    profile = orthographies.get(normalized_orthography)
                    if isinstance(profile, dict):
                        contract.update(copy.deepcopy(profile))

    return contract
