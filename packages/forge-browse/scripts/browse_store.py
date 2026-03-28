from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from browse_support import append_event as append_state_event, ensure_state_layout as ensure_paths_layout, list_sessions, resolve_state_paths
from browse_paths import events_path, sessions_path, snapshots_dir, state_dir


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_state_layout(state_root: Path) -> None:
    state_dir(state_root).mkdir(parents=True, exist_ok=True)
    snapshots_dir(state_root).mkdir(parents=True, exist_ok=True)
    events_path(state_root).parent.mkdir(parents=True, exist_ok=True)
    ensure_paths_layout(resolve_state_paths(str(state_root)))


def _compat_document(paths: dict[str, str]) -> dict:
    sessions = {session["id"]: session for session in list_sessions(paths)}
    return {"version": "2.0", "sessions": sessions}


def _write_document(paths: dict[str, str], document: dict) -> None:
    sessions = document.get("sessions", {})
    if isinstance(sessions, dict):
        payload = {"sessions": list(sessions.values())}
    elif isinstance(sessions, list):
        payload = {"sessions": sessions}
    else:
        payload = {"sessions": []}
    Path(paths["sessions_path"]).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_sessions_document(state_root: Path) -> dict:
    ensure_state_layout(state_root)
    return _compat_document(resolve_state_paths(str(state_root)))


def save_sessions_document(state_root: Path, document: dict) -> None:
    ensure_state_layout(state_root)
    _write_document(resolve_state_paths(str(state_root)), document)


def ensure_session(document: dict, session_id: str, *, driver: str, state_root: Path) -> dict:
    sessions = document.setdefault("sessions", {})
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id,
            "label": session_id,
            "driver": driver,
            "browser": "chromium",
            "lang": None,
            "device": None,
            "status": "active",
            "created_at": _timestamp(),
            "updated_at": _timestamp(),
            "last_url": None,
            "last_artifact": None,
            "active_tab_id": None,
            "tabs": [],
            "artifacts_dir": str((snapshots_dir(state_root) / session_id).resolve()),
            "user_data_dir": str((snapshots_dir(state_root) / session_id / "user-data").resolve()),
            "storage_state_path": str((snapshots_dir(state_root) / session_id / "storage-state.json").resolve()),
        }
    return sessions[session_id]


def next_tab_id(session: dict) -> str:
    tabs = session.get("tabs") or []
    return str(len(tabs) + 1)


def record_tab(state_root: Path, session_id: str, *, driver: str, tab: dict) -> dict:
    document = load_sessions_document(state_root)
    session = ensure_session(document, session_id, driver=driver, state_root=state_root)
    tabs = [*(session.get("tabs") or []), tab]
    session["tabs"] = tabs
    session["active_tab_id"] = tab["tab_id"]
    session["driver"] = driver
    session["updated_at"] = _timestamp()
    save_sessions_document(state_root, document)
    paths = resolve_state_paths(str(state_root))
    append_state_event(
        paths,
        {
            "event": "open",
            "session_id": session_id,
            "tab_id": tab["tab_id"],
            "url": tab["url"],
            "artifact": tab.get("snapshot_path"),
        },
    )
    return session


def load_session(state_root: Path, session_id: str) -> dict:
    document = load_sessions_document(state_root)
    session = document.get("sessions", {}).get(session_id)
    if not isinstance(session, dict):
        raise ValueError(f"Unknown forge-browse session: {session_id}")
    return session


def append_event(state_root: Path, event: dict) -> None:
    ensure_state_layout(state_root)
    append_state_event(resolve_state_paths(str(state_root)), event)
