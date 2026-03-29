from __future__ import annotations

import json
from pathlib import Path

from common import timestamp_slug


def _load_status(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def update_change_status(
    *,
    status_path: Path,
    verification_path: Path,
    summary: str,
    slug: str,
    state: str | None,
    note: str | None,
    verified: str | None,
    residual_risk: list[str],
) -> dict:
    current = _load_status(status_path)
    notes = current.get("notes", [])
    if not isinstance(notes, list):
        notes = []
    if note:
        notes.append(note)
    verification = current.get("verification", {})
    if not isinstance(verification, dict):
        verification = {}
    if verified:
        verification["latest_result"] = verified
    if residual_risk:
        verification["residual_risk"] = residual_risk
    payload = {
        "slug": slug,
        "summary": summary,
        "state": state or current.get("state") or "proposed",
        "created_at": current.get("created_at") or timestamp_slug(),
        "updated_at": timestamp_slug(),
        "notes": notes,
        "verification": verification,
    }
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if note or verified or residual_risk:
        lines = ["## Update", "", f"- State: {payload['state']}"]
        if note:
            lines.append(f"- Note: {note}")
        if verified:
            lines.append(f"- Verified: {verified}")
        for item in residual_risk:
            lines.append(f"- Residual risk: {item}")
        with verification_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(["", *lines, ""]))
    return payload
