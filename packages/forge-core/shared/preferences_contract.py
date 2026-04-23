from __future__ import annotations

import copy
import json
from functools import lru_cache

from compat import compat_default_extra, filter_canonical_preferences, load_preferences_compat
from preferences_paths import OUTPUT_CONTRACTS_PATH, PREFERENCES_SCHEMA_PATH
from text_utils import normalize_choice_token, repair_text_artifacts


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

CANONICAL_OPTIONAL_STRING_FIELDS = (
    "language",
    "orthography",
    "tone_detail",
    "output_quality",
)
CANONICAL_LIST_FIELDS = ("custom_rules",)


@lru_cache(maxsize=1)
def load_preferences_schema() -> dict:
    return json.loads(PREFERENCES_SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_output_contract_profiles() -> dict | None:
    if not OUTPUT_CONTRACTS_PATH.exists():
        return None
    payload = json.loads(OUTPUT_CONTRACTS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def preference_defaults() -> dict[str, object]:
    defaults: dict[str, object] = {}
    for key, config in load_preferences_schema().get("properties", {}).items():
        default_value = config.get("default")
        if isinstance(default_value, (str, list)):
            defaults[key] = copy.deepcopy(default_value)
    for key, value in compat_default_extra(load_preferences_compat()).items():
        if key not in defaults:
            defaults[key] = copy.deepcopy(value)
    return defaults


def resolve_output_contract(preferences: object) -> dict[str, object]:
    if not isinstance(preferences, dict):
        return {}

    contract: dict[str, object] = {}
    profiles = load_output_contract_profiles()
    language_profile: dict[str, object] | None = None

    language = preferences.get("language")
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

    orthography = preferences.get("orthography")
    if isinstance(orthography, str) and orthography.strip():
        normalized_orthography = normalize_choice_token(orthography)
        contract["orthography"] = normalized_orthography
        if isinstance(profiles, dict):
            orthographies = profiles.get("orthographies")
            if isinstance(orthographies, dict):
                profile = orthographies.get(normalized_orthography)
                if isinstance(profile, dict):
                    contract.update(copy.deepcopy(profile))

    tone_detail = preferences.get("tone_detail")
    if isinstance(tone_detail, str) and tone_detail.strip():
        contract["tone_detail"] = tone_detail.strip()

    custom_rules = preferences.get("custom_rules")
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


def normalize_preferences(
    payload: object,
    *,
    strict: bool = False,
    include_defaults: bool = True,
) -> tuple[dict[str, object], list[str]]:
    defaults = preference_defaults() if include_defaults else {}
    warnings: list[str] = []
    if payload is None:
        return defaults, warnings

    payload = filter_canonical_preferences(payload)
    if not isinstance(payload, dict):
        raise ValueError("Preferences payload must be a JSON object.")

    properties = load_preferences_schema().get("properties", {})
    normalized = copy.deepcopy(defaults)
    allowed_keys = set(properties)

    for key in sorted(payload):
        if key not in allowed_keys:
            message = f"Ignored unknown preference '{key}'."
            if strict:
                raise ValueError(message)
            warnings.append(message)
            continue

        raw_value = payload[key]
        if key in PREFERENCE_ALIASES:
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
            continue

        if key in CANONICAL_OPTIONAL_STRING_FIELDS:
            if not isinstance(raw_value, str):
                message = f"Preference '{key}' must be a string."
                if strict:
                    raise ValueError(message)
                warnings.append(message)
                continue
            value = repair_text_artifacts(raw_value.strip())
            if not isinstance(value, str) or not value:
                message = f"Preference '{key}' must be a non-empty string."
                if strict:
                    raise ValueError(message)
                warnings.append(message)
                continue
            normalized[key] = value
            continue

        if key in CANONICAL_LIST_FIELDS:
            if not isinstance(raw_value, list):
                message = f"Preference '{key}' must be a list of strings."
                if strict:
                    raise ValueError(message)
                warnings.append(message)
                continue
            values = [
                repaired
                for item in raw_value
                if isinstance(item, str)
                for repaired in [repair_text_artifacts(item.strip())]
                if isinstance(repaired, str) and repaired
            ]
            if not values:
                normalized.pop(key, None)
                continue
            normalized[key] = values
            continue

        message = f"Preference '{key}' is not supported."
        if strict:
            raise ValueError(message)
        warnings.append(message)

    return normalized, warnings
