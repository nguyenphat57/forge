from __future__ import annotations

import sys
from pathlib import Path


_SHARED_SUFFIXES = (
    ("packages", "forge-core", "shared"),
    ("forge-core", "shared"),
    ("shared",),
)
_CUSTOMIZE_SHARED_SUFFIXES = (
    ("packages", "forge-skills", "customize", "shared"),
    ("forge-skills", "customize", "shared"),
)


def _add_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def bootstrap_command_paths() -> Path:
    command_dir = Path(__file__).resolve().parent
    _add_path(command_dir)
    core_shared: Path | None = None
    for parent in command_dir.parents:
        for suffix in _SHARED_SUFFIXES:
            candidate = parent.joinpath(*suffix)
            if candidate.is_dir():
                core_shared = candidate
                break
        if core_shared is not None:
            break
    if core_shared is None:
        raise SystemExit(f"Missing forge-core shared runtime support near: {command_dir}")
    _add_path(core_shared)
    for parent in command_dir.parents:
        for suffix in _CUSTOMIZE_SHARED_SUFFIXES:
            candidate = parent.joinpath(*suffix)
            if candidate.is_dir():
                _add_path(candidate)
                return core_shared
    return core_shared
