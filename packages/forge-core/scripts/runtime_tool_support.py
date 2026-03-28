from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNTIME_TOOL_REGISTRY_ENV = "FORGE_RUNTIME_TOOLS_PATH"

RUNTIME_TOOL_SPECS = {
    "forge-browse": {
        "entry_script": Path("scripts") / "forge_browse.py",
        "env_var": "FORGE_BROWSE_ROOT",
    },
    "forge-design": {
        "entry_script": Path("scripts") / "forge_design.py",
        "env_var": "FORGE_DESIGN_ROOT",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def available_runtime_tool_names() -> tuple[str, ...]:
    return tuple(RUNTIME_TOOL_SPECS)


def runtime_tool_spec(bundle_name: str) -> dict[str, object]:
    if bundle_name not in RUNTIME_TOOL_SPECS:
        raise KeyError(f"Unknown runtime tool bundle: {bundle_name}")
    return RUNTIME_TOOL_SPECS[bundle_name]


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _load_manifest_state(bundle_root: Path) -> dict:
    for manifest_name in ("INSTALL-MANIFEST.json", "BUILD-MANIFEST.json"):
        manifest = _load_json(bundle_root / manifest_name)
        if manifest is None:
            continue
        state = manifest.get("state")
        if isinstance(state, dict):
            return state
    return {}


def resolve_runtime_tools_registry_path(bundle_root: Path | None = None) -> Path | None:
    env_value = os.environ.get(RUNTIME_TOOL_REGISTRY_ENV)
    if isinstance(env_value, str) and env_value.strip():
        return Path(env_value).expanduser().resolve()

    resolved_bundle_root = (bundle_root or ROOT_DIR).resolve()
    state = _load_manifest_state(resolved_bundle_root)
    registry_value = state.get("runtime_tools_path")
    if isinstance(registry_value, str) and registry_value.strip():
        return Path(registry_value).expanduser().resolve()

    relative_value = state.get("runtime_tools_relative_path")
    if isinstance(relative_value, str) and relative_value.strip():
        return (resolved_bundle_root / relative_value).resolve()

    root_value = state.get("root")
    if isinstance(root_value, str) and root_value.strip():
        return (Path(root_value).expanduser().resolve() / "state" / "runtime-tools.json").resolve()
    return None


def load_runtime_tool_registry(registry_path: Path | None) -> dict[str, object]:
    if registry_path is None:
        return {"version": 1, "tools": {}}
    payload = _load_json(registry_path)
    if payload is None:
        return {"version": 1, "tools": {}}
    tools = payload.get("tools")
    if not isinstance(tools, dict):
        payload["tools"] = {}
    return payload


def inspect_runtime_tool_target(bundle_name: str, target: Path) -> dict[str, object]:
    spec = runtime_tool_spec(bundle_name)
    target_path = target.expanduser().resolve()
    runtime_json_path = target_path / "runtime.json"
    script_path = target_path / Path(str(spec["entry_script"]))
    if not runtime_json_path.exists():
        return {"status": "FAIL", "bundle": bundle_name, "target": str(target_path), "error": "Missing runtime.json"}
    if not script_path.exists():
        return {
            "status": "FAIL",
            "bundle": bundle_name,
            "target": str(target_path),
            "error": f"Missing entry script: {spec['entry_script']}",
        }
    payload = _load_json(runtime_json_path)
    if payload is None:
        return {"status": "FAIL", "bundle": bundle_name, "target": str(target_path), "error": "Invalid runtime.json"}
    if payload.get("name") != bundle_name:
        return {"status": "FAIL", "bundle": bundle_name, "target": str(target_path), "error": "Runtime bundle name mismatch"}
    if payload.get("host") != "runtime":
        return {"status": "FAIL", "bundle": bundle_name, "target": str(target_path), "error": "Runtime bundle host mismatch"}
    return {
        "status": "PASS",
        "bundle": bundle_name,
        "target": str(target_path),
        "runtime_json_path": str(runtime_json_path),
        "script_path": str(script_path),
    }


def write_runtime_tool_registration(registry_path: Path, bundle_name: str, target: str | Path) -> dict[str, object]:
    inspection = inspect_runtime_tool_target(bundle_name, Path(target))
    if inspection["status"] != "PASS":
        raise ValueError(str(inspection.get("error") or f"Invalid runtime tool target for {bundle_name}"))
    payload = load_runtime_tool_registry(registry_path)
    payload["version"] = 1
    payload["updated_at"] = utc_now()
    tools = payload.setdefault("tools", {})
    record = {
        "bundle": bundle_name,
        "target": inspection["target"],
        "script_path": inspection["script_path"],
        "runtime_json_path": inspection["runtime_json_path"],
        "registered_at": utc_now(),
    }
    tools[bundle_name] = record
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def _candidate_targets(bundle_name: str, explicit_target: str | None, bundle_root: Path) -> list[tuple[str, Path]]:
    spec = runtime_tool_spec(bundle_name)
    candidates: list[tuple[str, Path]] = []
    seen: set[str] = set()

    def add_candidate(source: str, value: str | Path | None) -> None:
        if value is None:
            return
        candidate = Path(value).expanduser().resolve()
        marker = str(candidate)
        if marker in seen:
            return
        seen.add(marker)
        candidates.append((source, candidate))

    add_candidate("explicit", explicit_target)
    add_candidate("env", os.environ.get(str(spec["env_var"])))
    registry = load_runtime_tool_registry(resolve_runtime_tools_registry_path(bundle_root))
    tools = registry.get("tools")
    if isinstance(tools, dict):
        record = tools.get(bundle_name)
        if isinstance(record, dict):
            add_candidate("registry", record.get("target"))
    add_candidate("bundle-neighbor", bundle_root.parent / bundle_name)
    return candidates


def resolve_runtime_tool(bundle_name: str, *, explicit_target: str | None = None, bundle_root: Path | None = None) -> dict[str, object]:
    resolved_bundle_root = (bundle_root or ROOT_DIR).resolve()
    registry_path = resolve_runtime_tools_registry_path(resolved_bundle_root)
    last_error: str | None = None
    for source, candidate in _candidate_targets(bundle_name, explicit_target, resolved_bundle_root):
        inspection = inspect_runtime_tool_target(bundle_name, candidate)
        if inspection["status"] == "PASS":
            inspection["resolution_source"] = source
            inspection["registry_path"] = str(registry_path) if registry_path is not None else None
            return inspection
        last_error = str(inspection.get("error") or "Unknown runtime resolution error")
    return {
        "status": "FAIL",
        "bundle": bundle_name,
        "error": last_error or f"Unable to resolve runtime tool: {bundle_name}",
        "registry_path": str(registry_path) if registry_path is not None else None,
    }
