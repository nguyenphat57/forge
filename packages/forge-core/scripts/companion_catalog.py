from __future__ import annotations

import json
import os
from pathlib import Path

from common import ROOT_DIR
from companion_registry import load_companion_registry, registered_companion_targets, resolve_companion_registry_path


COMPANION_PATHS_ENV_VAR = "FORGE_COMPANION_PATHS"


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    raw_paths = os.environ.get(COMPANION_PATHS_ENV_VAR, "")
    for raw_path in raw_paths.split(os.pathsep):
        if raw_path.strip():
            roots.append(Path(raw_path).expanduser().resolve())
    registry = load_companion_registry(resolve_companion_registry_path())
    roots.extend(registered_companion_targets(registry))
    for candidate in (
        ROOT_DIR.parent,
        ROOT_DIR.parent.parent / "packages",
        ROOT_DIR.parent.parent / "dist",
    ):
        if candidate.exists():
            roots.append(candidate.resolve())
    ordered: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        ordered.append(root)
    return ordered


def _package_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    manifest_path = root / "companion.json"
    if manifest_path.exists():
        return [root]
    return [path for path in sorted(root.iterdir()) if path.is_dir() and (path / "companion.json").exists()]


def load_companion_specs() -> list[dict]:
    specs: list[dict] = []
    seen: set[str] = set()
    for root in _candidate_roots():
        for package_dir in _package_dirs(root):
            manifest_path = package_dir / "companion.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                continue
            capabilities_rel = manifest.get("capabilities_path") or "data/companion-capabilities.json"
            capabilities_path = package_dir / str(capabilities_rel)
            if not capabilities_path.exists():
                continue
            capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
            package_name = str(manifest.get("name") or package_dir.name)
            if package_name in seen:
                continue
            seen.add(package_name)
            specs.append(
                {
                    "name": package_name,
                    "host": manifest.get("host"),
                    "kind": manifest.get("kind"),
                    "package_dir": package_dir,
                    "manifest_path": manifest_path,
                    "capabilities_path": capabilities_path,
                    "capabilities": capabilities if isinstance(capabilities, dict) else {},
                }
            )
    return specs
