from __future__ import annotations

import copy
import json
import os
from functools import lru_cache
from pathlib import Path

from compat import (
    extract_extras,
    filter_canonical_preferences,
    load_preferences_compat,
    merge_extra_preferences,
    preferences_compat_matches,
    resolve_extra_preferences,
)
from style_maps import resolve_response_style
from text_utils import normalize_choice_token


ROOT_DIR = Path(__file__).resolve().parent.parent
PREFERENCES_SCHEMA_PATH = ROOT_DIR / "data" / "preferences-schema.json"
OUTPUT_CONTRACTS_PATH = ROOT_DIR / "data" / "output-contracts.json"
INSTALL_MANIFEST_PATH = ROOT_DIR / "INSTALL-MANIFEST.json"
DEFAULT_FALLBACK_STATE_ROOT = Path.home() / ".forge"
GLOBAL_PREFERENCES_RELATIVE_PATH = Path("state") / "preferences.json"
GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH = Path("state") / "extra_preferences.json"
LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH = Path(".brain") / "preferences.json"

PREFERENCE_ALIASES = {
    "technical_level": {
        "newbie": "newbie",
        "beginner": "newbie",
        "basic": "basic",
        "default": "basic",
        "standard": "basic",
        "intermediate": "basic",
        "technical": "technical",
        "developer": "technical",
        "advanced": "technical",
        "expert": "technical",
    },
    "detail_level": {
        "concise": "concise",
        "brief": "concise",
        "short": "concise",
        "balanced": "balanced",
        "default": "balanced",
        "normal": "balanced",
        "standard": "balanced",
        "detailed": "detailed",
        "detail": "detailed",
        "verbose": "detailed",
        "deep": "detailed",
        "thorough": "detailed",
    },
    "autonomy_level": {
        "guided": "guided",
        "low": "guided",
        "careful": "guided",
        "balanced": "balanced",
        "default": "balanced",
        "standard": "balanced",
        "autonomous": "autonomous",
        "proactive": "autonomous",
        "high": "autonomous",
        "independent": "autonomous",
    },
    "pace": {
        "steady": "steady",
        "slow": "steady",
        "careful": "steady",
        "balanced": "balanced",
        "default": "balanced",
        "normal": "balanced",
        "standard": "balanced",
        "fast": "fast",
        "rapid": "fast",
        "quick": "fast",
        "push": "fast",
    },
    "feedback_style": {
        "gentle": "gentle",
        "soft": "gentle",
        "encouraging": "gentle",
        "balanced": "balanced",
        "default": "balanced",
        "standard": "balanced",
        "direct": "direct",
        "blunt": "direct",
        "strict": "direct",
    },
    "personality": {
        "default": "default",
        "mentor": "mentor",
        "strict-coach": "strict-coach",
        "strict_coach": "strict-coach",
        "strict coach": "strict-coach",
    },
}


@lru_cache(maxsize=1)
def load_preferences_schema() -> dict:
    return json.loads(PREFERENCES_SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_output_contract_profiles() -> dict | None:
    if not OUTPUT_CONTRACTS_PATH.exists():
        return None
    payload = json.loads(OUTPUT_CONTRACTS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def preference_defaults() -> dict[str, str]:
    schema = load_preferences_schema()
    defaults: dict[str, str] = {}
    for key, config in schema.get("properties", {}).items():
        default_value = config.get("default")
        if isinstance(default_value, str):
            defaults[key] = default_value
    return defaults


@lru_cache(maxsize=1)
def load_install_manifest() -> dict | None:
    if not INSTALL_MANIFEST_PATH.exists():
        return None
    manifest = json.loads(INSTALL_MANIFEST_PATH.read_text(encoding="utf-8"))
    return manifest if isinstance(manifest, dict) else None


def resolve_output_contract(extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return {}

    contract: dict[str, object] = {}
    profiles = load_output_contract_profiles()
    language_profile: dict[str, object] | None = None

    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = normalize_choice_token(language)
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
        normalized_orthography = normalize_choice_token(orthography)
        contract["orthography"] = normalized_orthography
        if isinstance(profiles, dict):
            orthographies = profiles.get("orthographies")
            if isinstance(orthographies, dict):
                profile = orthographies.get(normalized_orthography)
                if isinstance(profile, dict):
                    contract.update(copy.deepcopy(profile))

    tone_detail = extra.get("tone_detail")
    if isinstance(tone_detail, str) and tone_detail.strip():
        contract["tone_detail"] = tone_detail.strip()

    custom_rules = extra.get("custom_rules")
    if isinstance(custom_rules, list):
        normalized_rules = [item.strip() for item in custom_rules if isinstance(item, str) and item.strip()]
        if normalized_rules:
            contract["custom_rules"] = normalized_rules

    if "orthography" not in contract and isinstance(language_profile, dict):
        default_orthography = language_profile.get("default_orthography")
        if isinstance(default_orthography, str) and default_orthography.strip():
            normalized_orthography = normalize_choice_token(default_orthography)
            contract["orthography"] = normalized_orthography
            if isinstance(profiles, dict):
                orthographies = profiles.get("orthographies")
                if isinstance(orthographies, dict):
                    profile = orthographies.get(normalized_orthography)
                    if isinstance(profile, dict):
                        contract.update(copy.deepcopy(profile))

    return contract


def resolve_installed_state_root() -> Path | None:
    manifest = load_install_manifest()
    if manifest is not None:
        state = manifest.get("state")
        if isinstance(state, dict):
            root = state.get("root")
            if isinstance(root, str) and root.strip():
                return Path(root).expanduser().resolve()

    if ROOT_DIR.parent.name == "skills":
        return (ROOT_DIR.parent.parent / ROOT_DIR.name).resolve()

    return None


def resolve_installed_preferences_path() -> Path | None:
    manifest = load_install_manifest()
    if manifest is not None:
        state = manifest.get("state")
        if isinstance(state, dict):
            path = state.get("preferences_path")
            if isinstance(path, str) and path.strip():
                return Path(path).expanduser().resolve()

    state_root = resolve_installed_state_root()
    if state_root is None:
        return None
    return state_root / GLOBAL_PREFERENCES_RELATIVE_PATH


def resolve_installed_extra_preferences_path() -> Path | None:
    installed_preferences_path = resolve_installed_preferences_path()
    if installed_preferences_path is not None:
        return installed_preferences_path.with_name(GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH.name)

    state_root = resolve_installed_state_root()
    if state_root is None:
        return None
    return state_root / GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH


def resolve_forge_home(forge_home: Path | str | None = None) -> Path:
    candidate = forge_home if forge_home is not None else os.environ.get("FORGE_HOME")
    if candidate is not None:
        return Path(candidate).expanduser().resolve()
    installed_state_root = resolve_installed_state_root()
    if installed_state_root is not None:
        return installed_state_root
    return DEFAULT_FALLBACK_STATE_ROOT.resolve()


def resolve_global_preferences_path(forge_home: Path | str | None = None) -> Path:
    if forge_home is None and os.environ.get("FORGE_HOME") is None:
        installed_preferences_path = resolve_installed_preferences_path()
        if installed_preferences_path is not None:
            return installed_preferences_path
    return resolve_forge_home(forge_home) / GLOBAL_PREFERENCES_RELATIVE_PATH


def resolve_global_extra_preferences_path(forge_home: Path | str | None = None) -> Path:
    if forge_home is None and os.environ.get("FORGE_HOME") is None:
        installed_extra_path = resolve_installed_extra_preferences_path()
        if installed_extra_path is not None:
            return installed_extra_path
    return resolve_forge_home(forge_home) / GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH


def resolve_workspace_preferences_path(workspace: Path | None = None) -> Path:
    root = Path(workspace).resolve() if workspace is not None else Path.cwd()
    return root / LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH


def normalize_preferences(payload: object, *, strict: bool = False) -> tuple[dict[str, str], list[str]]:
    defaults = preference_defaults()
    warnings: list[str] = []
    if payload is None:
        return defaults, warnings

    payload = filter_canonical_preferences(payload)
    if not isinstance(payload, dict):
        raise ValueError("Preferences payload must be a JSON object.")

    properties = load_preferences_schema().get("properties", {})
    normalized = defaults.copy()
    allowed_keys = set(properties)

    for key in sorted(payload):
        if key not in allowed_keys:
            message = f"Ignored unknown preference '{key}'."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        raw_value = payload[key]
        if not isinstance(raw_value, str):
            message = f"Preference '{key}' must be a string."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        token = normalize_choice_token(raw_value)
        aliases = PREFERENCE_ALIASES.get(key, {})
        canonical = aliases.get(token)
        if canonical is None:
            allowed = ", ".join(properties[key].get("enum", []))
            message = f"Preference '{key}' must be one of: {allowed}."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        normalized[key] = canonical

    return normalized, warnings


def _read_json_payload(path: Path, *, strict: bool, label: str) -> tuple[object, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"Invalid JSON in {label}: {path}") from exc
        return None, [f"Invalid JSON in {path.name}. Using defaults."]


def _build_preferences_report(
    *,
    primary_payload: object,
    extra_payload: object | None,
    source_type: str,
    source_path: Path,
    strict: bool,
    warnings: list[str],
) -> dict:
    compat = load_preferences_compat()
    if extra_payload is not None:
        extra = resolve_extra_preferences(extra_payload, compat_config=compat)
    else:
        extra = resolve_extra_preferences(primary_payload, compat_config=compat)
    canonical_payload = filter_canonical_preferences(primary_payload, compat_config=compat)
    preferences, normalization_warnings = normalize_preferences(canonical_payload, strict=strict)
    warnings.extend(normalization_warnings)
    return {
        "preferences": preferences,
        "extra": extra,
        "source": {"type": source_type, "path": str(source_path)},
        "output_contract": resolve_output_contract(extra),
        "warnings": warnings,
    }


def load_preferences(
    *,
    preferences_file: Path | None = None,
    workspace: Path | None = None,
    strict: bool = False,
    forge_home: Path | str | None = None,
) -> dict:
    warnings: list[str] = []
    defaults = preference_defaults()

    if preferences_file is not None:
        explicit_path = Path(preferences_file).resolve()
        if not explicit_path.exists():
            raise FileNotFoundError(f"Preferences file does not exist: {explicit_path}")

        source_type = "explicit"
        source_path = explicit_path
        primary_payload = None
        extra_payload = None

        if explicit_path.name == GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH.name:
            extra_payload, extra_warnings = _read_json_payload(explicit_path, strict=strict, label="extra preferences file")
            warnings.extend(extra_warnings)
            sibling_preferences = explicit_path.with_name(GLOBAL_PREFERENCES_RELATIVE_PATH.name)
            if sibling_preferences.exists():
                primary_payload, primary_warnings = _read_json_payload(
                    sibling_preferences,
                    strict=strict,
                    label="preferences file",
                )
                warnings.extend(primary_warnings)
        else:
            primary_payload, primary_warnings = _read_json_payload(explicit_path, strict=strict, label="preferences file")
            warnings.extend(primary_warnings)
            if explicit_path.name == GLOBAL_PREFERENCES_RELATIVE_PATH.name:
                sibling_extra = explicit_path.with_name(GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH.name)
                if sibling_extra.exists():
                    extra_payload, extra_warnings = _read_json_payload(
                        sibling_extra,
                        strict=strict,
                        label="extra preferences file",
                    )
                    warnings.extend(extra_warnings)

        return _build_preferences_report(
            primary_payload=primary_payload,
            extra_payload=extra_payload,
            source_type=source_type,
            source_path=source_path,
            strict=strict,
            warnings=warnings,
        )

    global_path = resolve_global_preferences_path(forge_home)
    global_extra_path = resolve_global_extra_preferences_path(forge_home)
    if global_path.exists() or global_extra_path.exists():
        primary_payload = None
        extra_payload = None
        if global_path.exists():
            primary_payload, primary_warnings = _read_json_payload(global_path, strict=strict, label="preferences file")
            warnings.extend(primary_warnings)
        if global_extra_path.exists():
            extra_payload, extra_warnings = _read_json_payload(
                global_extra_path,
                strict=strict,
                label="extra preferences file",
            )
            warnings.extend(extra_warnings)
        source_path = global_path if global_path.exists() else global_extra_path
        return _build_preferences_report(
            primary_payload=primary_payload,
            extra_payload=extra_payload,
            source_type="global",
            source_path=source_path,
            strict=strict,
            warnings=warnings,
        )

    path = resolve_workspace_preferences_path(workspace) if workspace is not None else None
    if path is None or not path.exists():
        compat = load_preferences_compat()
        extra = resolve_extra_preferences(None, compat_config=compat)
        return {
            "preferences": defaults,
            "extra": extra,
            "source": {"type": "defaults", "path": None},
            "output_contract": resolve_output_contract(extra),
            "warnings": warnings,
        }

    payload, payload_warnings = _read_json_payload(path, strict=strict, label="preferences file")
    warnings.extend(payload_warnings)
    return _build_preferences_report(
        primary_payload=payload,
        extra_payload=None,
        source_type="workspace-legacy",
        source_path=path,
        strict=strict,
        warnings=warnings,
    )


def _apply_flat_extra_updates(base: dict[str, object], updates: dict[str, object] | None) -> dict[str, object]:
    merged = copy.deepcopy(base)
    for key, value in (updates or {}).items():
        if value is None:
            merged.pop(key, None)
            continue
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = merge_extra_preferences(existing, value)
            continue
        merged[key] = copy.deepcopy(value)
    return merged


def _payload_has_legacy_embedded_extras(payload: object, compat: dict | None) -> bool:
    if not isinstance(payload, dict):
        return False
    if preferences_compat_matches(payload, compat):
        return True
    return bool(extract_extras(payload, compat_config=compat))


def write_preferences(
    *,
    workspace: Path | None = None,
    updates: dict[str, str],
    extra_updates: dict[str, object] | None = None,
    strict: bool = False,
    replace: bool = False,
    apply: bool = False,
    forge_home: Path | str | None = None,
) -> dict:
    if not updates and not extra_updates:
        raise ValueError("At least one preference update is required.")

    workspace_path = Path(workspace).resolve() if workspace is not None else None
    forge_home_path = resolve_forge_home(forge_home)
    existing = load_preferences(workspace=workspace_path, strict=strict, forge_home=forge_home_path)
    base = preference_defaults() if replace else existing["preferences"].copy()
    base.update(updates)
    preferences, warnings = normalize_preferences(base, strict=strict)

    path = resolve_global_preferences_path(forge_home_path)
    extra_path = resolve_global_extra_preferences_path(forge_home_path)

    raw_payload = None
    raw_extra_payload = None
    if path.exists():
        try:
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw_payload = None
    if extra_path.exists():
        try:
            raw_extra_payload = json.loads(extra_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw_extra_payload = None

    compat = load_preferences_compat()
    serialized_preferences = copy.deepcopy(preferences)

    if raw_extra_payload is not None:
        persisted_extra = resolve_extra_preferences(raw_extra_payload, compat_config=compat)
    elif raw_payload is not None:
        persisted_extra = resolve_extra_preferences(raw_payload, compat_config=compat)
    else:
        persisted_extra = {}

    extra = _apply_flat_extra_updates(persisted_extra, extra_updates)

    changed_fields = [
        key for key in preferences if existing["preferences"].get(key) != preferences.get(key)
    ]
    changed_extra_fields = [
        key for key in (extra_updates or {})
        if existing["extra"].get(key) != extra.get(key)
    ]

    legacy_global_state_detected = (
        raw_payload is not None
        and raw_extra_payload is None
        and _payload_has_legacy_embedded_extras(raw_payload, compat)
    )

    created_file = not path.exists()
    created_extra_file = bool(extra) and not extra_path.exists()
    migrated_legacy_global_preferences = False

    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        if legacy_global_state_detected:
            backup_path = path.with_name(path.name + ".legacy.bak")
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            migrated_legacy_global_preferences = True
        path.write_text(json.dumps(serialized_preferences, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if extra:
            extra_path.parent.mkdir(parents=True, exist_ok=True)
            extra_path.write_text(json.dumps(extra, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        elif extra_path.exists():
            extra_path.unlink()

    status = "PASS" if changed_fields or changed_extra_fields else "WARN"
    if warnings and status == "PASS":
        status = "WARN"

    return {
        "status": status,
        "scope": "adapter-global",
        "state_root": str(forge_home_path),
        "forge_home": str(forge_home_path),
        "workspace": str(workspace_path) if workspace_path is not None else None,
        "path": str(path),
        "extra_path": str(extra_path),
        "applied": apply,
        "replace": replace,
        "created_file": created_file and apply,
        "created_extra_file": created_extra_file and apply,
        "migrated_legacy_workspace_preferences": existing["source"]["type"] == "workspace-legacy",
        "migrated_legacy_global_preferences": migrated_legacy_global_preferences,
        "previous_preferences": existing["preferences"],
        "previous_extra": existing["extra"],
        "preferences": preferences,
        "extra": extra,
        "output_contract": resolve_output_contract(extra),
        "response_style": resolve_response_style(preferences),
        "changed_fields": changed_fields,
        "changed_extra_fields": changed_extra_fields,
        "warnings": warnings,
    }
