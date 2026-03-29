from __future__ import annotations

import json
import shutil
from pathlib import Path

from common import timestamp_slug


def _append_brain_entries(brain_dir: Path, filename: str, kind: str, scope: str, values: list[str]) -> None:
    path = brain_dir / filename
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload if isinstance(payload, list) else []
    else:
        entries = []
    for value in values:
        entries.append(
            {
                "id": timestamp_slug(),
                "kind": kind,
                "scope": scope,
                "summary": value,
                "status": "active",
                "evidence": [],
                "next": [],
                "tags": ["change-archive"],
                "revisit_if": None,
                "trigger": "change-archive",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def archive_change(active_root: Path, archive_root: Path, *, decision: list[str], learning: list[str]) -> dict:
    if not active_root.exists():
        raise FileNotFoundError(f"Active change does not exist: {active_root}")
    archive_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(active_root), str(archive_root))
    status_path = archive_root / "status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    payload["state"] = "archived"
    payload["archived_at"] = timestamp_slug()
    status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    brain_dir = active_root.parents[3] / ".brain"
    _append_brain_entries(brain_dir, "decisions.json", "decision", payload.get("slug", "change"), decision)
    _append_brain_entries(brain_dir, "learnings.json", "learning", payload.get("slug", "change"), learning)
    return {"archive_root": str(archive_root), "change": payload}
