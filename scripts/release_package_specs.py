from __future__ import annotations

import json
from pathlib import Path


MANIFEST_FILES = (
    ("adapter", "adapter.json"),
    ("runtime", "runtime.json"),
)


def load_package_spec(package_dir: Path) -> dict | None:
    for kind, manifest_name in MANIFEST_FILES:
        manifest_path = package_dir / manifest_name
        if not manifest_path.exists():
            continue
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Package manifest must be an object: {manifest_path}")
        payload["kind"] = kind
        payload["package_dir"] = package_dir
        payload["manifest_path"] = manifest_path
        if kind == "adapter" and not payload.get("overlay_dir"):
            raise ValueError(f"Adapter manifest is missing overlay_dir: {manifest_path}")
        return payload
    return None


def discover_package_specs(packages_dir: Path) -> list[dict]:
    specs: list[dict] = []
    for package_dir in sorted(packages_dir.iterdir()):
        if not package_dir.is_dir() or package_dir.name == "forge-core":
            continue
        spec = load_package_spec(package_dir)
        if spec is not None:
            specs.append(spec)
    return specs
