from __future__ import annotations

import copy

from compat_paths import (
    compat_entry_paths,
    compat_extra_fields,
    compat_serialization_fields,
    get_nested_value,
    has_nested_value,
    load_preferences_compat,
    set_nested_value,
)
from compat_translation import compat_read_value, preferences_compat_matches
from text_utils import normalize_choice_token


def choose_compat_write_path(existing_payload: object, entry: dict) -> str | None:
    for path in compat_entry_paths(entry):
        if has_nested_value(existing_payload, path):
            return path
    paths = compat_entry_paths(entry)
    return paths[0] if paths else None


def compat_values_equivalent(existing_raw: object, desired_value: str, entry: dict) -> bool:
    existing_value = compat_read_value(existing_raw, entry)
    if not isinstance(existing_value, str):
        return False
    return normalize_choice_token(existing_value) == normalize_choice_token(desired_value)


def compat_write_value(existing_payload: object, desired_value: str, entry: dict) -> str:
    for path in compat_entry_paths(entry):
        existing_raw = get_nested_value(existing_payload, path)
        if compat_values_equivalent(existing_raw, desired_value, entry) and isinstance(existing_raw, str):
            return existing_raw

    token = normalize_choice_token(desired_value)
    write_map = entry.get("write_map")
    if isinstance(write_map, dict):
        mapped = write_map.get(token)
        if isinstance(mapped, str):
            return mapped
    return desired_value


def apply_extra_preferences(
    payload: object,
    extra_updates: dict[str, object] | None,
    *,
    existing_payload: object,
    compat: dict | None = None,
) -> object:
    if not isinstance(payload, dict) or not extra_updates:
        return payload

    compat_entries = compat_extra_fields(compat)
    for key, value in extra_updates.items():
        entry = compat_entries.get(key)
        if entry is not None:
            for path in compat_entry_paths(entry):
                from compat_paths import delete_nested_value

                delete_nested_value(payload, path)
            if value is None:
                continue
            path = choose_compat_write_path(existing_payload, entry)
            if path is None:
                continue
            if isinstance(value, str):
                serialized_value: object = compat_write_value(existing_payload, value, entry)
            else:
                serialized_value = copy.deepcopy(value)
            set_nested_value(payload, path, serialized_value)
            continue

        if value is None:
            payload.pop(key, None)
            continue
        payload[key] = copy.deepcopy(value)

    return payload


def _serialize_flat_preferences_payload(
    preferences: dict[str, str],
    *,
    existing_payload: object,
    extra_updates: dict[str, object] | None,
) -> object:
    serialized = copy.deepcopy(existing_payload) if isinstance(existing_payload, dict) else {}
    for key, value in preferences.items():
        serialized[key] = value
    return apply_extra_preferences(
        serialized,
        extra_updates,
        existing_payload=existing_payload,
    )


def serialize_preferences_payload(
    preferences: dict[str, str],
    *,
    existing_payload: object,
    replace: bool,
    extra_updates: dict[str, object] | None = None,
    compat_config: dict | None = None,
) -> object:
    compat = load_preferences_compat() if compat_config is None else compat_config
    if compat is None:
        return _serialize_flat_preferences_payload(
            preferences,
            existing_payload=existing_payload,
            extra_updates=extra_updates,
        )

    write_config = compat.get("write")
    fields = compat_serialization_fields(compat)
    if not fields:
        return _serialize_flat_preferences_payload(
            preferences,
            existing_payload=existing_payload,
            extra_updates=extra_updates,
        )

    use_compat = False
    if preferences_compat_matches(existing_payload, compat):
        use_compat = True
    elif isinstance(write_config, dict) and existing_payload is None and write_config.get("prefer_native_format"):
        use_compat = True

    if not use_compat:
        return _serialize_flat_preferences_payload(
            preferences,
            existing_payload=existing_payload,
            extra_updates=extra_updates,
        )

    template = write_config.get("template") if isinstance(write_config, dict) else None
    preserve_existing_payload = True
    if isinstance(write_config, dict):
        preserve_existing_payload = write_config.get("preserve_existing_payload", True)

    if isinstance(existing_payload, dict) and preserve_existing_payload:
        serialized = copy.deepcopy(existing_payload)
    elif isinstance(template, dict):
        serialized = copy.deepcopy(template)
    else:
        serialized = {}

    for key, desired_value in preferences.items():
        entry = fields.get(key)
        if not isinstance(entry, dict):
            continue
        path = choose_compat_write_path(existing_payload if not replace else serialized, entry)
        if path is None:
            continue
        value = compat_write_value(existing_payload if not replace else serialized, desired_value, entry)
        set_nested_value(serialized, path, value)

    return apply_extra_preferences(
        serialized,
        extra_updates,
        existing_payload=existing_payload if isinstance(existing_payload, dict) else serialized,
        compat=compat,
    )
