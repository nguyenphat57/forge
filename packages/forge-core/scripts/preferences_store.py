from __future__ import annotations

import copy
import json
from pathlib import Path

from compat import canonical_preference_keys, filter_canonical_preferences, load_preferences_compat, preferences_compat_matches
from preferences_contract import normalize_preferences, preference_defaults, resolve_output_contract
from preferences_paths import (
    GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH,
    GLOBAL_PREFERENCES_RELATIVE_PATH,
    resolve_forge_home,
    resolve_global_extra_preferences_path,
    resolve_global_preferences_path,
    resolve_workspace_preferences_path,
)
from style_maps import resolve_response_style


CANONICAL_PREFERENCE_KEYS = canonical_preference_keys()


def _read_json_payload(path: Path, *, strict: bool, label: str) -> tuple[object, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"Invalid JSON in {label}: {path}") from exc
        return None, [f"Invalid JSON in {path.name}. Using defaults."]


def _append_warning(warnings: list[str], warning: str) -> None:
    if warning not in warnings:
        warnings.append(warning)


def _normalize_scope_payload(payload: object, *, strict: bool) -> tuple[dict[str, object], list[str]]:
    compat = load_preferences_compat()
    canonical_payload = filter_canonical_preferences(payload, compat_config=compat)
    return normalize_preferences(canonical_payload, strict=strict, include_defaults=False)


def _merge_payloads(*payloads: object) -> object:
    merged: dict[str, object] = {}
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            merged[key] = copy.deepcopy(value)
    return merged


def _load_scope_state(
    path: Path,
    *,
    strict: bool,
    label: str,
    legacy_extra_path: Path | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    raw_payload = None
    raw_extra_payload = None

    if path.exists():
        raw_payload, payload_warnings = _read_json_payload(path, strict=strict, label=label)
        warnings.extend(payload_warnings)
    if legacy_extra_path is not None and legacy_extra_path.exists():
        raw_extra_payload, extra_warnings = _read_json_payload(
            legacy_extra_path,
            strict=strict,
            label=f"{label} legacy extra preferences file",
        )
        warnings.extend(extra_warnings)

    merged_payload = _merge_payloads(raw_payload, raw_extra_payload)
    preferences, normalization_warnings = _normalize_scope_payload(merged_payload, strict=strict)
    warnings.extend(normalization_warnings)
    compat = load_preferences_compat()

    return {
        "path": path,
        "extra_path": legacy_extra_path,
        "exists": path.exists() or bool(legacy_extra_path and legacy_extra_path.exists()),
        "raw_payload": raw_payload,
        "raw_extra_payload": raw_extra_payload,
        "preferences": preferences,
        "warnings": warnings,
        "legacy_split_detected": bool(legacy_extra_path and legacy_extra_path.exists()),
        "compat_detected": preferences_compat_matches(raw_payload, compat),
    }


def _resolve_source_type(
    *,
    explicit: bool,
    global_exists: bool,
    workspace_exists: bool,
) -> str:
    if explicit:
        return "explicit"
    if workspace_exists and global_exists:
        return "merged"
    if workspace_exists:
        return "workspace"
    if global_exists:
        return "global"
    return "defaults"


def _build_effective_report(
    *,
    defaults: dict[str, object],
    global_state: dict[str, object] | None,
    workspace_state: dict[str, object] | None,
    explicit_state: dict[str, object] | None,
    explicit_path: Path | None,
    workspace_path: Path | None,
    global_path: Path | None,
    warnings: list[str],
) -> dict[str, object]:
    if explicit_state is not None:
        resolved = copy.deepcopy(defaults)
        sources: dict[str, str] = {key: "default" for key in resolved}
        for key, value in explicit_state["preferences"].items():
            resolved[key] = copy.deepcopy(value)
            sources[key] = "explicit"
        return {
            "preferences": resolved,
            "sources": sources,
            "source": {"type": "explicit", "path": str(explicit_path) if explicit_path is not None else None},
            "paths": {
                "explicit": str(explicit_path) if explicit_path is not None else None,
                "global": str(global_path) if global_path is not None else None,
                "workspace": str(workspace_path) if workspace_path is not None else None,
            },
            "warnings": warnings,
            "scope_payloads": {
                "defaults": copy.deepcopy(defaults),
                "explicit": copy.deepcopy(explicit_state["preferences"]),
                "global": {},
                "workspace": {},
            },
            "legacy": {
                "global_split_detected": bool(explicit_state.get("legacy_split_detected")),
                "workspace_compat_detected": bool(explicit_state.get("compat_detected")),
            },
        }

    global_preferences = copy.deepcopy((global_state or {}).get("preferences", {}))
    workspace_preferences = copy.deepcopy((workspace_state or {}).get("preferences", {}))
    resolved = copy.deepcopy(defaults)
    sources: dict[str, str] = {key: "default" for key in resolved}

    for key, value in global_preferences.items():
        resolved[key] = copy.deepcopy(value)
        sources[key] = "global"
    for key, value in workspace_preferences.items():
        resolved[key] = copy.deepcopy(value)
        sources[key] = "workspace"

    for key in global_preferences:
        sources.setdefault(key, "global")
    for key in workspace_preferences:
        sources[key] = "workspace"

    source_type = _resolve_source_type(
        explicit=False,
        global_exists=bool((global_state or {}).get("exists")),
        workspace_exists=bool((workspace_state or {}).get("exists")),
    )
    source_path = None
    if source_type == "workspace":
        source_path = str(workspace_path) if workspace_path is not None else None
    elif source_type == "global":
        source_path = str(global_path) if global_path is not None else None
    elif source_type == "merged":
        source_path = str(workspace_path) if workspace_path is not None else None

    return {
        "preferences": resolved,
        "sources": sources,
        "source": {"type": source_type, "path": source_path},
        "paths": {
            "global": str(global_path) if global_path is not None else None,
            "workspace": str(workspace_path) if workspace_path is not None else None,
        },
        "warnings": warnings,
        "scope_payloads": {
            "defaults": copy.deepcopy(defaults),
            "global": global_preferences,
            "workspace": workspace_preferences,
        },
        "legacy": {
            "global_split_detected": bool((global_state or {}).get("legacy_split_detected")),
            "workspace_compat_detected": bool((workspace_state or {}).get("compat_detected")),
        },
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

    global_path = resolve_global_preferences_path(forge_home)
    global_extra_path = resolve_global_extra_preferences_path(forge_home)
    workspace_path = resolve_workspace_preferences_path(workspace) if workspace is not None else None

    explicit_state: dict[str, object] | None = None
    if preferences_file is not None:
        explicit_path = Path(preferences_file).resolve()
        if not explicit_path.exists():
            raise FileNotFoundError(f"Preferences file does not exist: {explicit_path}")

        if explicit_path.name == GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH.name:
            sibling_preferences = explicit_path.with_name(GLOBAL_PREFERENCES_RELATIVE_PATH.name)
            explicit_state = _load_scope_state(
                sibling_preferences,
                strict=strict,
                label="preferences file",
                legacy_extra_path=explicit_path,
            )
        else:
            sibling_extra = None
            if explicit_path.name == GLOBAL_PREFERENCES_RELATIVE_PATH.name:
                candidate = explicit_path.with_name(GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH.name)
                if candidate.exists():
                    sibling_extra = candidate
            explicit_state = _load_scope_state(
                explicit_path,
                strict=strict,
                label="preferences file",
                legacy_extra_path=sibling_extra,
            )
        warnings.extend(explicit_state["warnings"])
        report = _build_effective_report(
            defaults=defaults,
            global_state=None,
            workspace_state=None,
            explicit_state=explicit_state,
            explicit_path=explicit_path,
            workspace_path=workspace_path,
            global_path=global_path,
            warnings=warnings,
        )
        report["output_contract"] = resolve_output_contract(report["preferences"])
        return report

    global_state = _load_scope_state(
        global_path,
        strict=strict,
        label="preferences file",
        legacy_extra_path=global_extra_path,
    )
    warnings.extend(global_state["warnings"])

    workspace_state = None
    if workspace_path is not None:
        workspace_state = _load_scope_state(
            workspace_path,
            strict=strict,
            label="workspace preferences file",
            legacy_extra_path=None,
        )
        warnings.extend(workspace_state["warnings"])

    report = _build_effective_report(
        defaults=defaults,
        global_state=global_state,
        workspace_state=workspace_state,
        explicit_state=None,
        explicit_path=None,
        workspace_path=workspace_path,
        global_path=global_path,
        warnings=warnings,
    )
    report["output_contract"] = resolve_output_contract(report["preferences"])
    return report


def _normalize_updates(
    updates: dict[str, object],
    *,
    strict: bool,
) -> tuple[dict[str, object], list[str]]:
    return normalize_preferences(updates, strict=strict, include_defaults=False)


def _apply_scope_updates(
    base_payload: dict[str, object],
    updates: dict[str, object],
    clear_fields: set[str],
    *,
    replace: bool,
) -> dict[str, object]:
    payload = {} if replace else copy.deepcopy(base_payload)
    for field in clear_fields:
        payload.pop(field, None)
    for key, value in updates.items():
        payload[key] = copy.deepcopy(value)
    return payload


def _payload_is_flat_canonical(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    return set(payload).issubset(CANONICAL_PREFERENCE_KEYS)


def _backup_file(path: Path) -> Path:
    backup_path = path.with_name(path.name + ".legacy.bak")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def _write_scope_file(path: Path, payload: dict[str, object]) -> bool:
    if not payload:
        if path.exists():
            path.unlink()
            return True
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return not path.exists()


def _persist_scope_payload(path: Path, payload: dict[str, object]) -> tuple[bool, bool]:
    existed_before = path.exists()
    if not payload:
        if path.exists():
            path.unlink()
        return existed_before, False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return existed_before, True


def write_preferences(
    *,
    workspace: Path | None = None,
    updates: dict[str, object],
    clear_fields: set[str] | None = None,
    strict: bool = False,
    replace: bool = False,
    apply: bool = False,
    forge_home: Path | str | None = None,
    scope: str = "global",
) -> dict:
    clear_fields = set(clear_fields or set())
    if not updates and not clear_fields:
        raise ValueError("At least one preference update is required.")
    if scope not in {"global", "workspace", "both"}:
        raise ValueError("Scope must be one of: global, workspace, both.")

    workspace_path = Path(workspace).resolve() if workspace is not None else None
    if scope in {"workspace", "both"} and workspace_path is None:
        raise ValueError("Workspace scope requires --workspace.")

    forge_home_path = resolve_forge_home(forge_home)
    existing = load_preferences(workspace=workspace_path, strict=strict, forge_home=forge_home_path)
    warnings = list(existing.get("warnings", []))
    normalized_updates, normalization_warnings = _normalize_updates(updates, strict=strict)
    for warning in normalization_warnings:
        _append_warning(warnings, warning)

    invalid_clear_fields = sorted(field for field in clear_fields if field not in CANONICAL_PREFERENCE_KEYS)
    if invalid_clear_fields:
        message = f"Unknown preference fields: {', '.join(invalid_clear_fields)}."
        if strict:
            raise ValueError(message)
        warnings.append(message)
        clear_fields = {field for field in clear_fields if field in CANONICAL_PREFERENCE_KEYS}

    global_path = resolve_global_preferences_path(forge_home_path)
    global_extra_path = resolve_global_extra_preferences_path(forge_home_path)
    resolved_workspace_path = resolve_workspace_preferences_path(workspace_path) if workspace_path is not None else None
    base_global = copy.deepcopy(existing["scope_payloads"].get("global", {}))
    base_workspace = copy.deepcopy(existing["scope_payloads"].get("workspace", {}))
    previous_effective = copy.deepcopy(existing["preferences"])

    target_paths: list[str] = []
    created_targets: list[str] = []
    changed_fields: set[str] = set()
    migrated_legacy_global_preferences = False
    migrated_legacy_workspace_preferences = False

    next_global = copy.deepcopy(base_global)
    next_workspace = copy.deepcopy(base_workspace)

    if scope in {"global", "both"}:
        next_global = _apply_scope_updates(base_global, normalized_updates, clear_fields, replace=replace)
        target_paths.append(str(global_path))
        candidate_fields = set(normalized_updates) | clear_fields
        if replace:
            candidate_fields.update(base_global)
        for field in candidate_fields:
            if base_global.get(field) != next_global.get(field):
                changed_fields.add(field)

    if scope in {"workspace", "both"} and resolved_workspace_path is not None:
        next_workspace = _apply_scope_updates(base_workspace, normalized_updates, clear_fields, replace=replace)
        target_paths.append(str(resolved_workspace_path))
        candidate_fields = set(normalized_updates) | clear_fields
        if replace:
            candidate_fields.update(base_workspace)
        for field in candidate_fields:
            if base_workspace.get(field) != next_workspace.get(field):
                changed_fields.add(field)

    defaults = copy.deepcopy(existing["scope_payloads"].get("defaults", preference_defaults()))
    resolved_preferences = copy.deepcopy(defaults)
    resolved_sources: dict[str, str] = {key: "default" for key in resolved_preferences}
    for key, value in next_global.items():
        resolved_preferences[key] = copy.deepcopy(value)
        resolved_sources[key] = "global"
    for key, value in next_workspace.items():
        resolved_preferences[key] = copy.deepcopy(value)
        resolved_sources[key] = "workspace"

    if scope == "global" and resolved_workspace_path is not None:
        shadowed = sorted(set(normalized_updates) & set(base_workspace))
        if shadowed:
            warnings.append(f"Workspace overrides global for: {', '.join(shadowed)}.")

    if apply:
        if scope in {"global", "both"}:
            raw_global = existing.get("scope_payloads", {}).get("global", {})
            global_state = _load_scope_state(
                global_path,
                strict=False,
                label="preferences file",
                legacy_extra_path=global_extra_path,
            )
            raw_global_payload = global_state.get("raw_payload")
            raw_global_extra_payload = global_state.get("raw_extra_payload")
            needs_global_backup = bool(raw_global_extra_payload) or (
                raw_global_payload is not None and not _payload_is_flat_canonical(raw_global_payload)
            )
            if needs_global_backup and global_path.exists():
                _backup_file(global_path)
                migrated_legacy_global_preferences = True
            if raw_global_extra_payload is not None and global_extra_path.exists():
                _backup_file(global_extra_path)
                migrated_legacy_global_preferences = True
            existed_before, persisted = _persist_scope_payload(global_path, next_global)
            if not existed_before and persisted:
                created_targets.append(str(global_path))
            if global_extra_path.exists():
                global_extra_path.unlink()

        if scope in {"workspace", "both"} and resolved_workspace_path is not None:
            workspace_state = _load_scope_state(
                resolved_workspace_path,
                strict=False,
                label="workspace preferences file",
            )
            raw_workspace_payload = workspace_state.get("raw_payload")
            needs_workspace_backup = raw_workspace_payload is not None and not _payload_is_flat_canonical(raw_workspace_payload)
            if needs_workspace_backup and resolved_workspace_path.exists():
                _backup_file(resolved_workspace_path)
                migrated_legacy_workspace_preferences = True
            existed_before, persisted = _persist_scope_payload(resolved_workspace_path, next_workspace)
            if not existed_before and persisted:
                created_targets.append(str(resolved_workspace_path))

    status = "PASS" if changed_fields else "WARN"
    if warnings and status == "PASS":
        status = "WARN"

    return {
        "status": status,
        "scope": scope,
        "state_root": str(forge_home_path),
        "forge_home": str(forge_home_path),
        "workspace": str(workspace_path) if workspace_path is not None else None,
        "targets": target_paths,
        "applied": apply,
        "replace": replace,
        "created_targets": created_targets,
        "migrated_legacy_workspace_preferences": migrated_legacy_workspace_preferences,
        "migrated_legacy_global_preferences": migrated_legacy_global_preferences,
        "previous_preferences": previous_effective,
        "preferences": resolved_preferences,
        "sources": resolved_sources,
        "output_contract": resolve_output_contract(resolved_preferences),
        "response_style": resolve_response_style(resolved_preferences),
        "changed_fields": sorted(changed_fields),
        "warnings": warnings,
    }
