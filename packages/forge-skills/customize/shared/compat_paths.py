from __future__ import annotations

import copy
import json
import os
from functools import lru_cache
from pathlib import Path


BUNDLE_ROOT_ENV_VAR = "FORGE_BUNDLE_ROOT"
HOST_BUNDLE_NAMES = ("forge-antigravity", "forge-codex", "forge-core")


def resolve_bundle_root() -> Path:
    override = os.environ.get(BUNDLE_ROOT_ENV_VAR)
    if isinstance(override, str) and override.strip():
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def resolve_adjacent_host_bundle_root(bundle_root: Path) -> Path | None:
    if bundle_root.name != "forge-customize":
        return None

    sibling_root = bundle_root.parent
    preferred_names = HOST_BUNDLE_NAMES
    if sibling_root.parent.name != "antigravity":
        preferred_names = ("forge-codex", "forge-antigravity", "forge-core")

    for bundle_name in preferred_names:
        candidate = sibling_root / bundle_name
        if candidate.is_dir():
            return candidate.resolve()
    return None


def _resolve_compat_path() -> Path:
    host_runtime_root = resolve_adjacent_host_bundle_root(ROOT_DIR)
    if host_runtime_root is not None:
        candidate = host_runtime_root / "data" / "preferences-compat.json"
        if candidate.exists():
            return candidate
    return ROOT_DIR / "data" / "preferences-compat.json"


ROOT_DIR = resolve_bundle_root()
PREFERENCES_COMPAT_PATH = _resolve_compat_path()
CANONICAL_PREFERENCE_KEYS = (
    "technical_level",
    "detail_level",
    "autonomy_level",
    "pace",
    "feedback_style",
    "personality",
    "language",
    "orthography",
    "tone_detail",
    "output_quality",
    "custom_rules",
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


def canonical_preference_keys() -> set[str]:
    return set(CANONICAL_PREFERENCE_KEYS)


def compat_canonical_paths(compat: dict | None) -> set[str]:
    if not isinstance(compat, dict):
        return set()
    read_config = compat.get("read")
    paths: set[str] = set()
    if isinstance(read_config, dict):
        fields = read_config.get("canonical_fields")
        if isinstance(fields, dict):
            for entry in fields.values():
                if isinstance(entry, dict):
                    paths.update(compat_entry_paths(entry))
    for entry in compat_extra_fields(compat).values():
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
