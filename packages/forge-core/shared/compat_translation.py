from __future__ import annotations

import copy

from compat_paths import (
    canonical_preference_keys,
    compat_canonical_paths,
    compat_default_extra,
    compat_entry_paths,
    compat_extra_fields,
    delete_nested_value,
    get_nested_value,
    load_preferences_compat,
)
from text_utils import normalize_choice_token, repair_text_artifacts


def preferences_compat_matches(payload: object, compat: dict | None = None) -> bool:
    if not isinstance(payload, dict):
        return False
    compat = load_preferences_compat() if compat is None else compat
    if compat is None:
        return False

    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return False

    match_any = read_config.get("match_any_top_level_keys")
    if isinstance(match_any, list):
        if any(isinstance(key, str) and key in payload for key in match_any):
            return True

    match_all = read_config.get("match_all_top_level_keys")
    if isinstance(match_all, list):
        keys = [key for key in match_all if isinstance(key, str)]
        if keys and all(key in payload for key in keys):
            return True

    return False


def compat_read_value(raw_value: object, entry: dict) -> object:
    if not isinstance(raw_value, str):
        return raw_value

    token = normalize_choice_token(raw_value)
    read_map = entry.get("read_map")
    if isinstance(read_map, dict):
        mapped = read_map.get(token)
        if mapped is not None:
            return mapped
    return raw_value


def translate_preferences_payload(payload: object, compat: dict | None = None) -> object:
    compat = load_preferences_compat() if compat is None else compat
    if compat is None or not preferences_compat_matches(payload, compat):
        return payload

    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return payload

    translated: dict[str, object] = {}
    fields = read_config.get("canonical_fields")
    if isinstance(fields, dict):
        for key, entry in fields.items():
            if not isinstance(entry, dict):
                continue
            for path in compat_entry_paths(entry):
                raw_value = get_nested_value(payload, path)
                if raw_value is None:
                    continue
                translated[key] = compat_read_value(raw_value, entry)
                break

    for key, entry in compat_extra_fields(compat).items():
        for path in compat_entry_paths(entry):
            raw_value = get_nested_value(payload, path)
            if raw_value is None:
                continue
            translated[key] = copy.deepcopy(compat_read_value(raw_value, entry))
            break

    return translated


def merge_extra_preferences(
    base: dict[str, object] | None,
    override: dict[str, object] | None,
) -> dict[str, object]:
    merged: dict[str, object] = copy.deepcopy(base or {})
    for key, value in (override or {}).items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = merge_extra_preferences(existing, value)
            continue
        merged[key] = copy.deepcopy(value)
    return merged


def extract_extras(raw_payload: object, compat_config: dict | None = None) -> dict[str, object]:
    if not isinstance(raw_payload, dict):
        return {}

    compat = load_preferences_compat() if compat_config is None else compat_config
    if preferences_compat_matches(raw_payload, compat):
        extras = copy.deepcopy(raw_payload)
        for path in compat_canonical_paths(compat):
            delete_nested_value(extras, path)
        compat_extras: dict[str, object] = {}
        for key, entry in compat_extra_fields(compat).items():
            for path in compat_entry_paths(entry):
                raw_value = get_nested_value(raw_payload, path)
                if raw_value is None:
                    continue
                compat_extras[key] = copy.deepcopy(compat_read_value(raw_value, entry))
                delete_nested_value(extras, path)
                break
        return repair_text_artifacts(merge_extra_preferences(extras, compat_extras))

    canonical_keys = canonical_preference_keys()
    return repair_text_artifacts({
        key: copy.deepcopy(value)
        for key, value in raw_payload.items()
        if key not in canonical_keys
    })


def filter_canonical_preferences(raw_payload: object, compat_config: dict | None = None) -> object:
    if not isinstance(raw_payload, dict):
        return raw_payload

    compat = load_preferences_compat() if compat_config is None else compat_config
    if preferences_compat_matches(raw_payload, compat):
        return translate_preferences_payload(raw_payload, compat)

    return copy.deepcopy(raw_payload)


def resolve_extra_preferences(
    raw_payload: object,
    *,
    compat_config: dict | None = None,
    include_defaults: bool = True,
) -> dict[str, object]:
    compat = load_preferences_compat() if compat_config is None else compat_config
    extra = extract_extras(raw_payload, compat_config=compat)
    if not include_defaults:
        return extra
    return merge_extra_preferences(compat_default_extra(compat), extra)
