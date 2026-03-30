from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, timestamp_slug


VALID_KINDS = ("decision", "learning")
VALID_STATUSES = ("active", "resolved", "superseded")


def resolve_target(brain_dir: Path, kind: str) -> Path:
    mapping = {
        "decision": brain_dir / "decisions.json",
        "learning": brain_dir / "learnings.json",
    }
    return mapping[kind]


def load_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if isinstance(data, list):
        return data
    raise ValueError(f"{path} must contain a JSON array.")


def build_entry(args: argparse.Namespace) -> dict:
    next_steps = [item for item in args.next_step if isinstance(item, str) and item.strip()]
    summary = args.summary.strip()
    tags = list(args.tag)
    if args.constitution and "constitution-lite" not in tags:
        tags.append("constitution-lite")
    return {
        "id": timestamp_slug(),
        "kind": args.kind,
        "scope": args.scope,
        "summary": summary,
        "status": args.status,
        "evidence": args.evidence,
        "next": next_steps,
        "tags": tags,
        "revisit_if": args.revisit_if,
        "trigger": args.trigger,
        "resume_hint": next_steps[0] if next_steps else args.revisit_if or "Re-open this item when the work slice resumes.",
    }


def format_text(path: Path, entry: dict, total: int) -> str:
    lines = [
        "Forge Continuity Capture",
        f"- File: {path}",
        f"- Kind: {entry['kind']}",
        f"- Scope: {entry['scope']}",
        f"- Status: {entry['status']}",
        f"- Summary: {entry['summary']}",
        f"- Resume hint: {entry['resume_hint']}",
        f"- Total entries: {total}",
    ]
    for label, values in (
        ("Evidence", entry["evidence"]),
        ("Next", entry["next"]),
        ("Tags", entry["tags"]),
    ):
        if values:
            lines.append(f"- {label}:")
            for value in values:
                lines.append(f"  - {value}")
        else:
            lines.append(f"- {label}: (none)")
    lines.append(f"- Revisit if: {entry['revisit_if'] or '(none)'}")
    lines.append(f"- Trigger: {entry['trigger'] or '(none)'}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Capture scoped Forge continuity items into .brain JSON files.")
    parser.add_argument("summary", help="Short decision or learning summary")
    parser.add_argument("--kind", required=True, choices=VALID_KINDS, help="Entry kind")
    parser.add_argument("--scope", required=True, help="Module, feature, or subsystem scope")
    parser.add_argument("--status", default="resolved", choices=VALID_STATUSES, help="Entry status")
    parser.add_argument("--evidence", action="append", default=[], help="Evidence source or verification note. Repeatable.")
    parser.add_argument("--next", dest="next_step", action="append", default=[], help="Next action linked to this entry. Repeatable.")
    parser.add_argument("--tag", action="append", default=[], help="Optional tag. Repeatable.")
    parser.add_argument("--constitution", action="store_true", help="Also tag this decision as constitution-lite")
    parser.add_argument("--revisit-if", default=None, help="Condition that should reopen or invalidate this item")
    parser.add_argument("--trigger", default=None, help="Trigger or repeated failure pattern that produced this item")
    parser.add_argument("--brain-dir", type=Path, default=Path.cwd() / ".brain", help="Target .brain directory")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    brain_dir = args.brain_dir.resolve()
    brain_dir.mkdir(parents=True, exist_ok=True)
    path = resolve_target(brain_dir, args.kind)
    entries = load_entries(path)
    entry = build_entry(args)
    entries.append(entry)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "file": str(path),
        "entry": entry,
        "total_entries": len(entries),
    }
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(path, entry, len(entries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
