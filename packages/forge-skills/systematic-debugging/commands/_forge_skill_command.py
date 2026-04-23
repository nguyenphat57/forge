from __future__ import annotations

import sys
from pathlib import Path


_SHARED_SUFFIXES = (
    ("packages", "forge-core", "shared"),
    ("forge-core", "shared"),
    ("shared",),
)


def _add_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def bootstrap_command_paths() -> Path:
    command_dir = Path(__file__).resolve().parent
    _add_path(command_dir)
    for parent in command_dir.parents:
        for suffix in _SHARED_SUFFIXES:
            candidate = parent.joinpath(*suffix)
            if candidate.is_dir():
                _add_path(candidate)
                return candidate
    raise SystemExit(f"Missing forge-core shared runtime support near: {command_dir}")
