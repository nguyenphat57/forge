from __future__ import annotations

import copy
import json
from functools import lru_cache

from compat import filter_canonical_preferences
from preferences_paths import OUTPUT_CONTRACTS_PATH, PREFERENCES_SCHEMA_PATH
from text_utils import normalize_choice_token, normalize_text


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

DEFAULT_DELEGATION_PREFERENCE = "auto"
DELEGATION_PREFERENCE_ALIASES = {
    "off": "off",
    "none": "off",
    "disabled": "off",
    "disable": "off",
    "sequential": "off",
    "auto": "auto",
    "default": "auto",
    "review": "review-lanes",
    "reviewer": "review-lanes",
    "reviewers": "review-lanes",
    "review-lane": "review-lanes",
    "review-lanes": "review-lanes",
    "review-lane-subagents": "review-lanes",
    "parallel": "parallel-workers",
    "parallel-worker": "parallel-workers",
    "parallel-workers": "parallel-workers",
    "full": "parallel-workers",
}
LEGACY_DELEGATION_RULE_MARKERS = {
    normalize_text("Delegated: Spawn subagents để tăng tiến độ khi cần"),
    normalize_text("Delegated: Spawn subagents de tang tien do khi can"),
    normalize_text("Delegated: Spawn subagents when needed"),
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
    defaults: dict[str, str] = {}
    for key, config in load_preferences_schema().get("properties", {}).items():
        default_value = config.get("default")
        if isinstance(default_value, str):
            defaults[key] = default_value
    return defaults


def normalize_delegation_preference(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return DELEGATION_PREFERENCE_ALIASES.get(normalize_choice_token(value))


def detect_legacy_delegation_preference(extra: object) -> str | None:
    if not isinstance(extra, dict):
        return None
    custom_rules = extra.get("custom_rules")
    if not isinstance(custom_rules, list):
        return None
    for item in custom_rules:
        if not isinstance(item, str) or not item.strip():
            continue
        if normalize_text(item) in LEGACY_DELEGATION_RULE_MARKERS:
            return DEFAULT_DELEGATION_PREFERENCE
    return None


def resolve_delegation_preference(
    extra: object,
    *,
    strict: bool = False,
) -> tuple[str, list[str], str]:
    warnings: list[str] = []
    source = "default"
    explicit = None
    if isinstance(extra, dict):
        explicit = extra.get("delegation_preference")
    normalized = normalize_delegation_preference(explicit)
    if normalized is not None:
        return normalized, warnings, "explicit"

    if explicit is not None:
        message = "Delegation preference must be one of: off, auto, review-lanes, parallel-workers."
        if strict:
            raise ValueError(message)
        warnings.append(message)

    legacy = detect_legacy_delegation_preference(extra)
    if legacy is not None:
        warnings.append("legacy_delegation_rule_detected")
        source = "legacy-custom-rules"
        return legacy, warnings, source

    return DEFAULT_DELEGATION_PREFERENCE, warnings, source


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
