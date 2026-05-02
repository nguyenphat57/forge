from __future__ import annotations

import json
from pathlib import Path

from common import timestamp_slug
from session_context_io import dedupe, string_list


ENTRY_LIMIT = 5


def has_closeout_signals(args: object) -> bool:
    return any(
        _arg_list(args, name)
        for name in ("pending", "verification", "risk", "blocker", "decision", "learning")
    )


def has_session_signals(args: object) -> bool:
    return any(_arg_list(args, name) for name in ("pending", "verification", "risk", "blocker"))


def handover_requested(args: object) -> bool:
    return bool(getattr(args, "write_handover", False) or _arg_list(args, "pending") or _arg_list(args, "blocker"))


def append_closeout_entries(brain_dir: Path, args: object, *, scope: str) -> list[str]:
    written: list[str] = []
    for kind, summaries in (("decision", _arg_list(args, "decision")), ("learning", _arg_list(args, "learning"))):
        if not summaries:
            continue
        path = _entry_path(brain_dir, kind)
        entries = _load_entries(path)
        changed = False
        for summary in summaries:
            entry, added = _upsert_entry(entries, kind, summary, args, scope=scope)
            changed = changed or added
            if not added:
                changed = _merge_entry(entry, args) or changed
        if changed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def relevant_brain_continuity(brain_dir: Path, warnings: list[str]) -> list[str]:
    items: list[str] = []
    for kind, label in (("decision", "Decision"), ("learning", "Learning")):
        path = _entry_path(brain_dir, kind)
        for entry in reversed(_load_entries_for_resume(path, warnings)):
            if not _is_relevant(entry):
                continue
            summary = str(entry.get("summary") or "").strip()
            if not summary:
                continue
            items.append(f"{label}: {summary}")
            if len(items) >= ENTRY_LIMIT:
                return items
    return items


def _arg_list(args: object, name: str) -> list[str]:
    return [item.strip() for item in getattr(args, name, []) if isinstance(item, str) and item.strip()]


def _entry_path(brain_dir: Path, kind: str) -> Path:
    return brain_dir / ("decisions.json" if kind == "decision" else "learnings.json")


def _load_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array.")
    return [entry for entry in data if isinstance(entry, dict)]


def _load_entries_for_resume(path: Path, warnings: list[str]) -> list[dict]:
    if not path.exists():
        return []
    try:
        return _load_entries(path)
    except (json.JSONDecodeError, ValueError):
        warnings.append(f"Invalid continuity JSON: {path}.")
        return []


def _upsert_entry(entries: list[dict], kind: str, summary: str, args: object, *, scope: str) -> tuple[dict, bool]:
    normalized = summary.strip()
    for entry in entries:
        if (
            str(entry.get("kind") or "").strip() == kind
            and str(entry.get("scope") or "").strip() == scope
            and str(entry.get("summary") or "").strip() == normalized
        ):
            return entry, False
    next_items = dedupe(_arg_list(args, "pending") + _arg_list(args, "blocker"))
    entry = {
        "id": timestamp_slug(),
        "kind": kind,
        "scope": scope,
        "summary": normalized,
        "status": "active" if kind == "learning" else "resolved",
        "evidence": _arg_list(args, "evidence") + _arg_list(args, "verification"),
        "next": next_items,
        "tags": _arg_list(args, "tag"),
        "revisit_if": None,
        "trigger": "closeout",
        "resume_hint": next_items[0] if next_items else "Re-open this item when the work slice resumes.",
    }
    entries.append(entry)
    return entry, True


def _merge_entry(entry: dict, args: object) -> bool:
    changed = False
    for key, values in (
        ("evidence", _arg_list(args, "evidence") + _arg_list(args, "verification")),
        ("next", _arg_list(args, "pending") + _arg_list(args, "blocker")),
        ("tags", _arg_list(args, "tag")),
    ):
        merged = dedupe(string_list(entry.get(key)) + values)
        if merged != string_list(entry.get(key)):
            entry[key] = merged
            changed = True
    if not str(entry.get("resume_hint") or "").strip():
        next_items = string_list(entry.get("next"))
        entry["resume_hint"] = next_items[0] if next_items else "Re-open this item when the work slice resumes."
        changed = True
    return changed


def _is_relevant(entry: dict) -> bool:
    status = str(entry.get("status") or "").strip().casefold()
    resume_hint = str(entry.get("resume_hint") or "").strip()
    return status == "active" or bool(resume_hint) or bool(string_list(entry.get("next")))
