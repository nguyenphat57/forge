from __future__ import annotations

import json
from pathlib import Path

import tomllib


def load_package_json(workspace: Path) -> dict:
    path = workspace / "package.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_pyproject(workspace: Path) -> dict:
    path = workspace / "pyproject.toml"
    if not path.exists():
        return {}
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def package_dependency_groups(package_json: dict) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        values = package_json.get(key)
        groups[key] = {name for name in values if isinstance(name, str) and name.strip()} if isinstance(values, dict) else set()
    return groups


def package_dependency_names(package_json: dict) -> set[str]:
    names: set[str] = set()
    for values in package_dependency_groups(package_json).values():
        names.update(values)
    return names


def read_env_example(workspace: Path) -> str:
    env_path = workspace / ".env.example"
    return env_path.read_text(encoding="utf-8") if env_path.exists() else ""


def has_any_path(workspace: Path, *relative_paths: str) -> bool:
    return any((workspace / relative_path).exists() for relative_path in relative_paths)
