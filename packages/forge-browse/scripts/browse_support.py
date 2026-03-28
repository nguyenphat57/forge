from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_MANIFEST_PATH = ROOT_DIR / "BUILD-MANIFEST.json"
INSTALL_MANIFEST_PATH = ROOT_DIR / "INSTALL-MANIFEST.json"
STATE_ROOT_ENV = "FORGE_BROWSE_STATE_ROOT"
DEFAULT_SESSIONS_RELATIVE_PATH = Path("state") / "sessions.json"
DEFAULT_EVENTS_RELATIVE_PATH = Path("state") / "events.jsonl"
DEFAULT_ARTIFACTS_RELATIVE_DIR = Path("artifacts")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _default_state_root() -> Path:
    return (ROOT_DIR.parent / "forge-browse-state").resolve()


def _build_state_root(state: dict | None) -> Path:
    if not isinstance(state, dict):
        return _default_state_root()
    dev_root = state.get("dev_root")
    if not isinstance(dev_root, dict):
        return _default_state_root()
    if dev_root.get("strategy") != "bundle-parent-relative":
        return _default_state_root()
    path_relative = dev_root.get("path_relative")
    if not isinstance(path_relative, str) or not path_relative.strip():
        return _default_state_root()
    return (ROOT_DIR.parent / Path(path_relative)).resolve()


def _materialize_install_state(state: dict | None) -> dict[str, str]:
    root = _default_state_root()
    if isinstance(state, dict):
        root_value = state.get("root")
        if isinstance(root_value, str) and root_value.strip():
            root = Path(root_value).expanduser().resolve()
    metadata = {
        "scope": (state or {}).get("scope") or "runtime-tool-global",
        "root": str(root),
    }
    for key, default in (
        ("sessions_path", root / DEFAULT_SESSIONS_RELATIVE_PATH),
        ("events_path", root / DEFAULT_EVENTS_RELATIVE_PATH),
        ("artifacts_dir", root / DEFAULT_ARTIFACTS_RELATIVE_DIR),
    ):
        value = (state or {}).get(key)
        metadata[key] = str(Path(value).expanduser().resolve()) if isinstance(value, str) and value.strip() else str(default)
    return metadata


def _materialize_build_state(state: dict | None) -> dict[str, str]:
    root = _build_state_root(state)
    metadata = {
        "scope": (state or {}).get("scope") or "runtime-tool-global",
        "root": str(root),
    }
    for key, default in (
        ("sessions_relative_path", DEFAULT_SESSIONS_RELATIVE_PATH),
        ("events_relative_path", DEFAULT_EVENTS_RELATIVE_PATH),
        ("artifacts_relative_dir", DEFAULT_ARTIFACTS_RELATIVE_DIR),
    ):
        value = (state or {}).get(key)
        relative = Path(value) if isinstance(value, str) and value.strip() else default
        suffix = "_path" if key.endswith("_path") else "_dir"
        metadata[key.replace("_relative", "")] = str((root / relative).resolve())
    return metadata


def _materialize_override_state(root_value: str) -> dict[str, str]:
    root = Path(root_value).expanduser().resolve()
    return {
        "scope": "runtime-tool-global",
        "root": str(root),
        "sessions_path": str((root / DEFAULT_SESSIONS_RELATIVE_PATH).resolve()),
        "events_path": str((root / DEFAULT_EVENTS_RELATIVE_PATH).resolve()),
        "artifacts_dir": str((root / DEFAULT_ARTIFACTS_RELATIVE_DIR).resolve()),
    }


def resolve_state_paths(explicit_root: str | None = None) -> dict[str, str]:
    if explicit_root and explicit_root.strip():
        return _materialize_override_state(explicit_root)
    override = os.environ.get(STATE_ROOT_ENV)
    if override and override.strip():
        return _materialize_override_state(override)
    install_manifest = _load_json(INSTALL_MANIFEST_PATH)
    if install_manifest is not None:
        return _materialize_install_state(install_manifest.get("state"))
    build_manifest = _load_json(BUILD_MANIFEST_PATH)
    return _materialize_build_state((build_manifest or {}).get("state"))


def ensure_state_layout(paths: dict[str, str]) -> dict[str, str]:
    root = Path(paths["root"])
    root.mkdir(parents=True, exist_ok=True)
    for key, value in paths.items():
        if key.endswith("_path"):
            Path(value).parent.mkdir(parents=True, exist_ok=True)
        elif key.endswith("_dir"):
            Path(value).mkdir(parents=True, exist_ok=True)
    return paths


def load_session_store(paths: dict[str, str]) -> dict[str, list[dict]]:
    sessions_path = Path(paths["sessions_path"])
    if not sessions_path.exists():
        return {"sessions": []}
    payload = json.loads(sessions_path.read_text(encoding="utf-8"))
    sessions = payload.get("sessions")
    return {"sessions": sessions if isinstance(sessions, list) else []}


def save_session_store(paths: dict[str, str], store: dict[str, list[dict]]) -> None:
    Path(paths["sessions_path"]).write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_event(paths: dict[str, str], event: dict[str, object]) -> None:
    with Path(paths["events_path"]).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def list_sessions(paths: dict[str, str]) -> list[dict]:
    return list(load_session_store(paths)["sessions"])


def get_session(paths: dict[str, str], session_id: str) -> dict:
    for session in list_sessions(paths):
        if session.get("id") == session_id:
            return session
    raise KeyError(f"Unknown forge-browse session: {session_id}")


def _session_runtime_paths(paths: dict[str, str], session_id: str) -> dict[str, str]:
    session_root = Path(paths["artifacts_dir"]) / session_id
    return {
        "artifacts_dir": str(session_root.resolve()),
        "user_data_dir": str((session_root / "user-data").resolve()),
        "storage_state_path": str((session_root / "storage-state.json").resolve()),
    }


def ensure_session(
    paths: dict[str, str],
    session_id: str,
    *,
    label: str,
    browser: str,
    lang: str | None,
    device: str | None,
) -> dict:
    store = load_session_store(paths)
    for session in store["sessions"]:
        if session.get("id") == session_id:
            return session

    runtime_paths = _session_runtime_paths(paths, session_id)
    Path(runtime_paths["artifacts_dir"]).mkdir(parents=True, exist_ok=True)
    Path(runtime_paths["user_data_dir"]).mkdir(parents=True, exist_ok=True)
    session = {
        "id": session_id,
        "label": label,
        "browser": browser,
        "lang": lang,
        "device": device,
        "status": "active",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "last_url": None,
        "last_artifact": None,
        "active_tab_id": None,
        "tabs": [],
        **runtime_paths,
    }
    store["sessions"].append(session)
    save_session_store(paths, store)
    append_event(paths, {"event": "session-create", "at": utc_now(), "session_id": session_id, "label": label})
    return session


def create_session(paths: dict[str, str], *, label: str, browser: str, lang: str | None, device: str | None) -> dict:
    session_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    return ensure_session(
        paths,
        session_id,
        label=label,
        browser=browser,
        lang=lang,
        device=device,
    )


def update_session(paths: dict[str, str], session_id: str, **updates: object) -> dict:
    store = load_session_store(paths)
    for session in store["sessions"]:
        if session.get("id") != session_id:
            continue
        session.update(updates)
        session["updated_at"] = utc_now()
        save_session_store(paths, store)
        return session
    raise KeyError(f"Unknown forge-browse session: {session_id}")


def close_session(paths: dict[str, str], session_id: str) -> dict:
    session = update_session(paths, session_id, status="closed")
    append_event(paths, {"event": "session-close", "at": utc_now(), "session_id": session_id})
    return session


def default_artifact_path(paths: dict[str, str], session_id: str, suffix: str) -> Path:
    artifact_dir = Path(get_session(paths, session_id)["artifacts_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return (artifact_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.{suffix}").resolve()
