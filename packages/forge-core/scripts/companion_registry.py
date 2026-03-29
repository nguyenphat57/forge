from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from common import resolve_forge_home


COMPANION_REGISTRY_ENV = "FORGE_COMPANIONS_PATH"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_companion_registry_path(forge_home: Path | None = None) -> Path:
    env_value = os.environ.get(COMPANION_REGISTRY_ENV)
    if isinstance(env_value, str) and env_value.strip():
        return Path(env_value).expanduser().resolve()
    return (resolve_forge_home(forge_home) / "state" / "companions.json").resolve()


def load_companion_registry(registry_path: Path) -> dict[str, object]:
    if not registry_path.exists():
        return {"version": 1, "companions": {}}
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"version": 1, "companions": {}}
    companions = payload.get("companions")
    if not isinstance(companions, dict):
        payload["companions"] = {}
    return payload


def inspect_companion_target(target: Path) -> dict[str, object]:
    target_path = target.expanduser().resolve()
    manifest_path = target_path / "companion.json"
    capabilities_path = target_path / "data" / "companion-capabilities.json"
    if not manifest_path.exists():
        return {"status": "FAIL", "target": str(target_path), "error": "Missing companion.json"}
    if not capabilities_path.exists():
        return {"status": "FAIL", "target": str(target_path), "error": "Missing data/companion-capabilities.json"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
    package_name = manifest.get("name")
    companion_id = capabilities.get("id")
    if not isinstance(package_name, str) or not package_name.strip():
        return {"status": "FAIL", "target": str(target_path), "error": "Invalid companion package name"}
    if not isinstance(companion_id, str) or not companion_id.strip():
        return {"status": "FAIL", "target": str(target_path), "error": "Invalid companion id"}
    return {
        "status": "PASS",
        "target": str(target_path),
        "package": package_name.strip(),
        "id": companion_id.strip(),
        "version": str(capabilities.get("version") or "unknown"),
        "manifest_path": str(manifest_path),
        "capabilities_path": str(capabilities_path),
    }


def write_companion_registration(registry_path: Path, target: Path) -> dict[str, object]:
    inspection = inspect_companion_target(target)
    if inspection["status"] != "PASS":
        raise ValueError(str(inspection.get("error") or "Invalid companion target"))
    payload = load_companion_registry(registry_path)
    payload["version"] = 1
    payload["updated_at"] = utc_now()
    companions = payload.setdefault("companions", {})
    record = {
        "id": inspection["id"],
        "package": inspection["package"],
        "target": inspection["target"],
        "version": inspection["version"],
        "registered_at": utc_now(),
    }
    companions[str(inspection["package"])] = record
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def find_companion_record(registry: dict[str, object], package_name: str) -> dict[str, object] | None:
    companions = registry.get("companions")
    if not isinstance(companions, dict):
        return None
    record = companions.get(package_name)
    return record if isinstance(record, dict) else None


def registered_companion_targets(registry: dict[str, object]) -> list[Path]:
    companions = registry.get("companions")
    if not isinstance(companions, dict):
        return []
    targets: list[Path] = []
    seen: set[Path] = set()
    for record in companions.values():
        if not isinstance(record, dict):
            continue
        target = record.get("target")
        if not isinstance(target, str) or not target.strip():
            continue
        path = Path(target).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        targets.append(path)
    return targets
