from __future__ import annotations

import json
import shutil
from pathlib import Path

from common import timestamp_slug
from verify_change_support import load_latest_verify_change


def _append_brain_entries(brain_dir: Path, filename: str, kind: str, scope: str, values: list[str], *, archive_root: Path) -> None:
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
                "status": "resolved",
                "evidence": [f"Archived change: {archive_root}"],
                "next": [],
                "tags": ["change-archive"],
                "revisit_if": None,
                "trigger": "change-archive",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def _merge_spec_index(workspace_root: Path, archive_root: Path, payload: dict) -> None:
    spec_files = sorted((archive_root / "specs").rglob("spec.md"))
    if not spec_files:
        return
    index_path = workspace_root / "docs" / "specs" / "change-index.json"
    if index_path.exists():
        existing = json.loads(index_path.read_text(encoding="utf-8"))
        entries = existing if isinstance(existing, list) else []
    else:
        entries = []
    known_paths = {item.get("archive_path") for item in entries if isinstance(item, dict)}
    latest_verify = payload.get("verification", {}).get("latest_verify_change") if isinstance(payload.get("verification"), dict) else None
    for spec_path in spec_files:
        if str(spec_path) in known_paths:
            continue
        entries.append(
            {
                "slug": payload.get("slug"),
                "summary": payload.get("summary"),
                "topic": spec_path.parent.name,
                "archived_at": payload.get("archived_at"),
                "archive_path": str(spec_path),
                "change_root": str(archive_root),
                "latest_verify_change": latest_verify,
            }
        )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def archive_change(active_root: Path, archive_root: Path, *, decision: list[str], learning: list[str]) -> dict:
    if not active_root.exists():
        raise FileNotFoundError(f"Active change does not exist: {active_root}")
    archive_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(active_root), str(archive_root))
    status_path = archive_root / "status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    payload["state"] = "archived"
    payload["archived_at"] = timestamp_slug()
    payload["archived_from"] = str(active_root)
    payload["resume_path"] = str(archive_root / "resume.md")
    workspace_root = active_root.parents[3]
    latest_verify = load_latest_verify_change(workspace_root, payload.get("slug"))
    if latest_verify is not None:
        verify_path, verify_payload = latest_verify
        verification = payload.get("verification", {})
        if not isinstance(verification, dict):
            verification = {}
        verification["latest_verify_change"] = {
            "path": str(verify_path),
            "status": verify_payload.get("status"),
            "decision": verify_payload.get("decision"),
        }
        payload["verification"] = verification
    status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    resume_path = archive_root / "resume.md"
    resume_path.write_text(
        "\n".join(
            [
                "# Archived Change",
                "",
                f"- Summary: {payload.get('summary', '(unknown)')}",
                f"- Archived from: {active_root}",
                f"- Archived at: {payload['archived_at']}",
                f"- Resume path: {archive_root}",
                f"- State: {payload['state']}",
            ]
        ),
        encoding="utf-8",
    )
    _merge_spec_index(workspace_root, archive_root, payload)
    brain_dir = workspace_root / ".brain"
    _append_brain_entries(brain_dir, "decisions.json", "decision", payload.get("slug", "change"), decision, archive_root=archive_root)
    _append_brain_entries(brain_dir, "learnings.json", "learning", payload.get("slug", "change"), learning, archive_root=archive_root)
    return {"archive_root": str(archive_root), "resume_path": str(resume_path), "change": payload}
