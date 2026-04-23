from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json_object(path: Path, label: str, warnings: list[str]) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warnings.append(f"Invalid JSON in {label}: {path}.")
        return None
    return payload if isinstance(payload, dict) else None


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in items:
        candidate = item.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        merged.append(candidate)
    return merged


def session_task(session: dict | None) -> str | None:
    if not isinstance(session, dict):
        return None
    working_on = session.get("working_on")
    if not isinstance(working_on, dict):
        return None
    for key in ("task", "feature"):
        value = working_on.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def session_files(session: dict | None) -> list[str]:
    if not isinstance(session, dict):
        return []
    working_on = session.get("working_on")
    if not isinstance(working_on, dict):
        return []
    return string_list(working_on.get("files"))


def session_blockers(session: dict | None) -> list[str]:
    if not isinstance(session, dict):
        return []
    for key in ("blockers", "blocker"):
        value = session.get(key)
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        if isinstance(value, list):
            return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def workspace_path_strings(workspace: Path, files: list[str]) -> list[str]:
    resolved: list[str] = []
    for file_name in files:
        candidate = Path(file_name)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        resolved.append(str(candidate))
    return resolved


def load_session(path: Path, warnings: list[str]) -> dict | None:
    if not path.exists():
        return None
    return read_json_object(path, "session context", warnings)


def build_handover_text(payload: dict, *, next_step: str | None) -> str:
    task = payload["working_on"]["task"] or payload["working_on"]["feature"] or "(none)"
    lines = [
        "HANDOVER",
        f"- Current task: {task}",
        f"- Status: {payload['working_on']['status'] or '(none)'}",
    ]
    _append_section(lines, "Pending", payload["pending_tasks"])
    _append_section(lines, "Verification run", payload["verification"])
    _append_section(lines, "Important decisions", payload["decisions_made"])
    _append_section(lines, "Risks", payload["risks"])
    _append_section(lines, "Blockers", string_list(payload.get("blockers")))
    lines.append(f"- Next step: {next_step or '(none)'}")
    return "\n".join(lines) + "\n"


def write_session(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_section(lines: list[str], label: str, values: list[str]) -> None:
    if not values:
        lines.append(f"- {label}: (none)")
        return
    lines.append(f"- {label}:")
    for item in values:
        lines.append(f"  - {item}")
