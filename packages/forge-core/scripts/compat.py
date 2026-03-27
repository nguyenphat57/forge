from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

from text_utils import normalize_choice_token


ROOT_DIR = Path(__file__).resolve().parent.parent
PREFERENCES_COMPAT_PATH = ROOT_DIR / "data" / "preferences-compat.json"
CANONICAL_PREFERENCE_KEYS = (
    "technical_level",
    "detail_level",
    "autonomy_level",
    "pace",
    "feedback_style",
    "personality",
)


@lru_cache(maxsize=1)
def load_preferences_compat() -> dict | None:
    if not PREFERENCES_COMPAT_PATH.exists():
        return None
    compat = json.loads(PREFERENCES_COMPAT_PATH.read_text(encoding="utf-8"))
    return compat if isinstance(compat, dict) else None


def compat_entry_paths(entry: dict) -> list[str]:
    paths = entry.get("paths")
    if not isinstance(paths, list):
        return []
    return [path for path in paths if isinstance(path, str) and path]


def get_nested_value(payload: object, path: str) -> object:
    if not isinstance(payload, dict):
        return None
    current: object = payload
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def has_nested_value(payload: object, path: str) -> bool:
    if not isinstance(payload, dict):
        return False
    current: object = payload
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return False
        current = current[segment]
    return True


def set_nested_value(payload: dict, path: str, value: object) -> None:
    segments = path.split(".")
    current = payload
    for segment in segments[:-1]:
        next_value = current.get(segment)
        if not isinstance(next_value, dict):
            next_value = {}
            current[segment] = next_value
        current = next_value
    current[segments[-1]] = value


def canonical_preference_keys() -> set[str]:
    return set(CANONICAL_PREFERENCE_KEYS)


def compat_canonical_paths(compat: dict | None) -> set[str]:
    if not isinstance(compat, dict):
        return set()
    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return set()
    fields = read_config.get("canonical_fields")
    if not isinstance(fields, dict):
        return set()
    paths: set[str] = set()
    for entry in fields.values():
        if isinstance(entry, dict):
            paths.update(compat_entry_paths(entry))
    return paths


def compat_serialization_fields(compat: dict | None) -> dict[str, dict]:
    if not isinstance(compat, dict):
        return {}

    write_config = compat.get("write")
    if isinstance(write_config, dict):
        fields = write_config.get("canonical_fields")
        if isinstance(fields, dict):
            return {key: value for key, value in fields.items() if isinstance(key, str) and isinstance(value, dict)}

    read_config = compat.get("read")
    if not isinstance(read_config, dict):
        return {}

    fields = read_config.get("canonical_fields")
    if not isinstance(fields, dict):
        return {}

    return {key: value for key, value in fields.items() if isinstance(key, str) and isinstance(value, dict)}


def compat_extra_fields(compat: dict | None) -> dict[str, dict]:
    if not isinstance(compat, dict):
        return {}
    extra_fields = compat.get("extra_fields")
    if not isinstance(extra_fields, dict):
        return {}
    return {key: value for key, value in extra_fields.items() if isinstance(key, str) and isinstance(value, dict)}


def compat_extra_paths(compat: dict | None) -> set[str]:
    paths: set[str] = set()
    for entry in compat_extra_fields(compat).values():
        paths.update(compat_entry_paths(entry))
    return paths


def compat_default_extra(compat: dict | None) -> dict[str, object]:
    if not isinstance(compat, dict):
        return {}

    default_extra = compat.get("default_extra")
    if not isinstance(default_extra, dict):
        return {}

    return copy.deepcopy(default_extra)


def delete_nested_value(payload: dict, path: str) -> None:
    segments = path.split(".")
    current = payload
    parents: list[tuple[dict, str]] = []

    for segment in segments[:-1]:
        next_value = current.get(segment)
        if not isinstance(next_value, dict):
            return
        parents.append((current, segment))
        current = next_value

    if segments[-1] not in current:
        return

    del current[segments[-1]]

    for parent, segment in reversed(parents):
        child = parent.get(segment)
        if isinstance(child, dict) and not child:
            del parent[segment]
            continue
        break


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

    fields = read_config.get("canonical_fields")
    if not isinstance(fields, dict):
        return payload

    translated: dict[str, object] = {}
    for key, entry in fields.items():
        if not isinstance(entry, dict):
            continue
        for path in compat_entry_paths(entry):
            raw_value = get_nested_value(payload, path)
            if raw_value is None:
                continue
            translated[key] = compat_read_value(raw_value, entry)
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
        return merge_extra_preferences(extras, compat_extras)

    canonical_keys = canonical_preference_keys()
    return {
        key: copy.deepcopy(value)
        for key, value in raw_payload.items()
        if key not in canonical_keys
    }


def filter_canonical_preferences(raw_payload: object, compat_config: dict | None = None) -> object:
    if not isinstance(raw_payload, dict):
        return raw_payload

    compat = load_preferences_compat() if compat_config is None else compat_config
    if preferences_compat_matches(raw_payload, compat):
        return translate_preferences_payload(raw_payload, compat)

    allowed_keys = canonical_preference_keys()
    return {key: raw_payload[key] for key in raw_payload if key in allowed_keys}


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
