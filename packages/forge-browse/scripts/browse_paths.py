from __future__ import annotations

import os
from pathlib import Path

from browse_support import STATE_ROOT_ENV, resolve_state_paths

STATE_SCOPE = "runtime-tool-global"
STATE_ENV_VAR = STATE_ROOT_ENV
LEGACY_STATE_ENV_VAR = "FORGE_BROWSE_HOME"


def bundle_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_state_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_value = os.environ.get(STATE_ENV_VAR) or os.environ.get(LEGACY_STATE_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path(resolve_state_paths()["root"])


def state_dir(state_root: Path) -> Path:
    return state_root / "state"


def sessions_path(state_root: Path) -> Path:
    return state_dir(state_root) / "sessions.json"


def events_path(state_root: Path) -> Path:
    return state_dir(state_root) / "events.jsonl"


def snapshots_dir(state_root: Path) -> Path:
    return state_root / "artifacts" / "snapshots"
