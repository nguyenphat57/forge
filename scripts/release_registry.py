from __future__ import annotations

import copy
import json
from pathlib import Path


def merge_json_overlay(base: object, overlay: object) -> object:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in overlay.items():
            if key in merged:
                merged[key] = merge_json_overlay(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged

    if isinstance(base, list) and isinstance(overlay, list):
        return [copy.deepcopy(item) for item in overlay]

    return copy.deepcopy(overlay)


def materialize_overlay_registry(core_dir: Path, overlay_dir: Path, destination: Path) -> None:
    overlay_path = overlay_dir / "data" / "orchestrator-registry.json"
    if not overlay_path.exists():
        return

    core_registry_path = core_dir / "data" / "orchestrator-registry.json"
    destination_path = destination / "data" / "orchestrator-registry.json"
    base = json.loads(core_registry_path.read_text(encoding="utf-8"))
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    merged = merge_json_overlay(base, overlay)
    destination_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
