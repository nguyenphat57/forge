from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_bundle_root(command_path: Path | None = None) -> Path:
    target = command_path or Path(__file__).resolve()
    return target.parents[1]


def _candidate_runtime_roots(bundle_root: Path) -> list[Path]:
    candidates: list[Path] = []
    env_root = os.environ.get("FORGE_BUNDLE_ROOT")
    if env_root:
        candidates.append(Path(env_root))

    if len(bundle_root.parents) >= 2:
        candidates.append(bundle_root.parents[1] / "forge-core")

    for name in ("forge-core", "forge-codex", "forge-antigravity"):
        candidates.append(bundle_root.parent / name)

    if bundle_root.parent.name == "skills":
        for name in ("forge-codex", "forge-antigravity"):
            candidates.append(bundle_root.parent / name)

    seen: set[Path] = set()
    normalized: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        normalized.append(resolved)
    return normalized


def bootstrap_shared_paths(command_path: Path | None = None) -> Path:
    target = command_path or Path(__file__).resolve()
    bundle_root = resolve_bundle_root(target)
    runtime_root = None
    for candidate in _candidate_runtime_roots(bundle_root):
        if (candidate / "shared").is_dir() and (candidate / "commands").is_dir():
            runtime_root = candidate
            break
    if runtime_root is None:
        raise SystemExit(f"Missing Forge runtime shared/commands for session owner: {bundle_root}")

    paths = [target.parent]
    source_customize_shared = runtime_root.parent / "forge-skills" / "customize" / "shared"
    if source_customize_shared.is_dir():
        paths.append(source_customize_shared)
    paths.extend([runtime_root / "shared", runtime_root / "commands"])
    for path in paths:
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)
    return runtime_root / "shared"
