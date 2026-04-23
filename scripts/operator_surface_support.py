from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from release_registry import merge_json_overlay


ROOT_DIR = Path(__file__).resolve().parent.parent
CORE_REGISTRY_PATH = ROOT_DIR / "packages" / "forge-core" / "data" / "orchestrator-registry.json"
OVERLAY_REGISTRY_PATHS = {
    "forge-antigravity": ROOT_DIR / "packages" / "forge-antigravity" / "overlay" / "data" / "orchestrator-registry.json",
    "forge-codex": ROOT_DIR / "packages" / "forge-codex" / "overlay" / "data" / "orchestrator-registry.json",
}
HOST_BY_BUNDLE = {
    "forge-antigravity": "antigravity",
    "forge-codex": "codex",
}
SESSION_MODE_LABELS = {
    "restore": "resume",
    "save": "save context",
    "handover": "handover",
}


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_core_registry() -> dict:
    registry = _load_json(CORE_REGISTRY_PATH)
    return registry if isinstance(registry, dict) else {}


@lru_cache(maxsize=None)
def load_bundle_registry(bundle_name: str) -> dict:
    registry = load_core_registry()
    overlay_path = OVERLAY_REGISTRY_PATHS.get(bundle_name)
    if overlay_path and overlay_path.exists():
        registry = merge_json_overlay(registry, _load_json(overlay_path))
    return registry


def _surface_section(registry: dict, section_name: str) -> dict:
    section = registry.get(section_name, {})
    if not isinstance(section, dict):
        return {"actions": {}, "session_modes": {}}
    actions = section.get("actions", {})
    session_modes = section.get("session_modes", {})
    return {
        "actions": actions if isinstance(actions, dict) else {},
        "session_modes": session_modes if isinstance(session_modes, dict) else {},
    }


def repo_operator_surface() -> dict:
    return _surface_section(load_core_registry(), "repo_operator_surface")


def host_operator_surface(bundle_name: str) -> dict:
    return _surface_section(load_bundle_registry(bundle_name), "host_operator_surface")


def host_name(bundle_name: str) -> str:
    return HOST_BY_BUNDLE[bundle_name]


def _host_values(metadata: dict, field: str, *, bundle_name: str) -> list[str]:
    values_by_host = metadata.get(field, {})
    if not isinstance(values_by_host, dict):
        return []
    values = values_by_host.get(host_name(bundle_name), [])
    if not isinstance(values, list):
        return []
    return [item for item in values if isinstance(item, str) and item.strip()]


def _workflow_label(path_text: str) -> str:
    return path_text.removeprefix("workflows/")


def _host_action_rows(bundle_name: str) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    for action_name, metadata in host_operator_surface(bundle_name)["actions"].items():
        if not isinstance(metadata, dict):
            continue
        hosts = metadata.get("hosts", [])
        if not isinstance(hosts, list) or host_name(bundle_name) not in hosts:
            continue
        rows.append((action_name, metadata))
    return rows


def render_operator_alias_rows(bundle_name: str) -> str:
    lines: list[str] = []
    for _, metadata in _host_action_rows(bundle_name):
        aliases = _host_values(metadata, "primary_aliases_by_host", bundle_name=bundle_name)
        if not aliases:
            continue
        alias = aliases[0]
        target = metadata.get("skill") or _workflow_label(metadata.get("workflow", ""))
        lines.append(f"| `{alias}` | `{target}` |")
    return "\n".join(lines)


def render_natural_language_examples(bundle_name: str) -> str:
    lines: list[str] = []
    for action_name, metadata in _host_action_rows(bundle_name):
        examples = _host_values(metadata, "natural_language_examples_by_host", bundle_name=bundle_name)
        if not examples:
            continue
        lines.append(f'- "{examples[0]}" -> `{action_name}`')
    return "\n".join(lines)


def render_repo_public_action_bullets() -> str:
    lines: list[str] = []
    for action_name in repo_operator_surface()["actions"]:
        lines.append(f"- `{action_name}`")
    return "\n".join(lines)


def render_session_request_examples(bundle_name: str) -> str:
    lines: list[str] = []
    metadata_root = load_bundle_registry(bundle_name).get("skill_catalog", {}).get("session-management", {})
    modes = metadata_root.get("session_modes", {}) if isinstance(metadata_root, dict) else {}
    for mode_name, metadata in modes.items():
        if not isinstance(metadata, dict):
            continue
        examples = _host_values(metadata, "natural_language_examples_by_host", bundle_name=bundle_name)
        if not examples:
            continue
        label = SESSION_MODE_LABELS.get(mode_name, mode_name)
        lines.append(f'- "{examples[0]}" -> `{label}`')
    return "\n".join(lines)


def _metadata_by_name(bundle_name: str, section_name: str, item_name: str) -> dict:
    section = host_operator_surface(bundle_name).get(section_name, {})
    metadata = section.get(item_name, {})
    return metadata if isinstance(metadata, dict) else {}


def render_contextual_placeholders(source_text: str, bundle_name: str, context: dict | None = None) -> str:
    del bundle_name, context
    return source_text


def render_registry_placeholders(source_text: str, bundle_name: str, context: dict | None = None) -> str:
    rendered = render_contextual_placeholders(source_text, bundle_name, context=context)
    replacements = {
        "{{FORGE_REPO_PUBLIC_ACTIONS}}": render_repo_public_action_bullets(),
        "{{FORGE_CODEX_OPERATOR_ALIAS_ROWS}}": render_operator_alias_rows("forge-codex"),
        "{{FORGE_CODEX_SESSION_REQUEST_EXAMPLES}}": render_session_request_examples("forge-codex"),
        "{{FORGE_ANTIGRAVITY_PRIMARY_OPERATOR_ALIAS_ROWS}}": render_operator_alias_rows("forge-antigravity"),
        "{{FORGE_ANTIGRAVITY_SESSION_REQUEST_EXAMPLES}}": render_session_request_examples("forge-antigravity"),
        "{{FORGE_CODEX_NATURAL_LANGUAGE_EXAMPLES}}": render_natural_language_examples("forge-codex"),
        "{{FORGE_ANTIGRAVITY_NATURAL_LANGUAGE_EXAMPLES}}": render_natural_language_examples("forge-antigravity"),
    }
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    return rendered

