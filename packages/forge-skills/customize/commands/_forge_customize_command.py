from __future__ import annotations

import sys
from pathlib import Path


def resolve_bundle_root(command_path: Path | None = None) -> Path:
    target = command_path or Path(__file__).resolve()
    return target.parents[1]


def bootstrap_shared_paths(command_path: Path | None = None) -> Path:
    target = command_path or Path(__file__).resolve()
    bundle_root = resolve_bundle_root(target)
    shared_dir = bundle_root / "shared"
    if not shared_dir.is_dir():
        raise SystemExit(f"Missing Forge customize shared runtime directory: {shared_dir}")

    paths = [shared_dir, target.parent]
    source_core_shared = bundle_root.parents[1] / "forge-core" / "shared"
    if source_core_shared.is_dir():
        paths.insert(0, source_core_shared)

    for path in paths:
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)
    return shared_dir
