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
SESSION_COMPATIBILITY_WRAPPERS = {
    "restore": "workflows/operator/recap.md",
    "save": "workflows/operator/save-brain.md",
    "handover": "workflows/operator/handover.md",
}


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_bundle_registry(bundle_name: str) -> dict:
    registry = _load_json(CORE_REGISTRY_PATH)
    overlay_path = OVERLAY_REGISTRY_PATHS.get(bundle_name)
    if overlay_path and overlay_path.exists():
        registry = merge_json_overlay(registry, _load_json(overlay_path))
    return registry


def operator_surface(bundle_name: str) -> dict:
    registry = load_bundle_registry(bundle_name)
    section = registry.get("operator_surface", {})
    if not isinstance(section, dict):
        return {"actions": {}, "session_modes": {}}
    actions = section.get("actions", {})
    session_modes = section.get("session_modes", {})
    return {
        "actions": actions if isinstance(actions, dict) else {},
        "session_modes": session_modes if isinstance(session_modes, dict) else {},
    }


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


def _primary_action_rows(bundle_name: str) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    for action_name, metadata in operator_surface(bundle_name)["actions"].items():
        if not isinstance(metadata, dict):
            continue
        aliases = _host_values(metadata, "primary_aliases_by_host", bundle_name=bundle_name)
        if not aliases:
            continue
        rows.append((action_name, metadata))
    return rows


def render_operator_alias_rows(bundle_name: str) -> str:
    lines: list[str] = []
    for _, metadata in _primary_action_rows(bundle_name):
        alias = _host_values(metadata, "primary_aliases_by_host", bundle_name=bundle_name)[0]
        workflow = metadata.get("workflow", "")
        lines.append(f"| `{alias}` | `{_workflow_label(workflow)}` |")
    return "\n".join(lines)


def render_codex_natural_language_examples() -> str:
    lines: list[str] = []
    for action_name, metadata in _primary_action_rows("forge-codex"):
        examples = _host_values(metadata, "natural_language_examples_by_host", bundle_name="forge-codex")
        if not examples:
            continue
        lines.append(f'- "{examples[0]}" -> `{action_name}`')
    return "\n".join(lines)


def render_codex_optional_aliases() -> str:
    lines: list[str] = []
    for _, metadata in _primary_action_rows("forge-codex"):
        alias = _host_values(metadata, "primary_aliases_by_host", bundle_name="forge-codex")[0]
        lines.append(f"- `{alias}`")
    return "\n".join(lines)


def render_antigravity_primary_wrapper_table() -> str:
    lines = [
        "| Surface | Wrapper | Core contract |",
        "|---------|---------|---------------|",
    ]
    for _, metadata in _primary_action_rows("forge-antigravity"):
        alias = _host_values(metadata, "primary_aliases_by_host", bundle_name="forge-antigravity")[0]
        workflow = metadata.get("workflow", "")
        core_contract = metadata.get("core_engine_entrypoint", "")
        lines.append(f"| `{alias}` | `{workflow}` | `{core_contract}` |")
    return "\n".join(lines)


def render_antigravity_compatibility_wrapper_table() -> str:
    lines = [
        "| Alias | Wrapper | Core contract |",
        "|-------|---------|---------------|",
    ]
    for mode_name, metadata in operator_surface("forge-antigravity")["session_modes"].items():
        if not isinstance(metadata, dict):
            continue
        aliases = _host_values(metadata, "compatibility_aliases_by_host", bundle_name="forge-antigravity")
        if not aliases:
            continue
        workflow = metadata.get("workflow", "")
        wrapper = SESSION_COMPATIBILITY_WRAPPERS.get(mode_name, workflow)
        lines.append(f"| `{aliases[0]}` | `{wrapper}` | `{workflow}` {mode_name} mode |")
    return "\n".join(lines)


def render_antigravity_compatibility_alias_rows() -> str:
    lines: list[str] = []
    for mode_name, metadata in operator_surface("forge-antigravity")["session_modes"].items():
        if not isinstance(metadata, dict):
            continue
        aliases = _host_values(metadata, "compatibility_aliases_by_host", bundle_name="forge-antigravity")
        if not aliases:
            continue
        wrapper = SESSION_COMPATIBILITY_WRAPPERS.get(mode_name, metadata.get("workflow", ""))
        lines.append(f"| `{aliases[0]}` | `{_workflow_label(wrapper)}` |")
    return "\n".join(lines)


def render_registry_placeholders(source_text: str, bundle_name: str) -> str:
    replacements = {
        "{{FORGE_CODEX_OPERATOR_ALIAS_ROWS}}": render_operator_alias_rows("forge-codex"),
        "{{FORGE_ANTIGRAVITY_PRIMARY_OPERATOR_ALIAS_ROWS}}": render_operator_alias_rows("forge-antigravity"),
        "{{FORGE_ANTIGRAVITY_COMPAT_OPERATOR_ALIAS_ROWS}}": render_antigravity_compatibility_alias_rows(),
        "{{FORGE_CODEX_NATURAL_LANGUAGE_EXAMPLES}}": render_codex_natural_language_examples(),
        "{{FORGE_CODEX_OPTIONAL_ALIASES}}": render_codex_optional_aliases(),
        "{{FORGE_ANTIGRAVITY_PRIMARY_WRAPPER_TABLE}}": render_antigravity_primary_wrapper_table(),
        "{{FORGE_ANTIGRAVITY_COMPATIBILITY_WRAPPER_TABLE}}": render_antigravity_compatibility_wrapper_table(),
    }
    rendered = source_text
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    return rendered
