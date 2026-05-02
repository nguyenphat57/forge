from __future__ import annotations

from _forge_session_command import bootstrap_shared_paths

bootstrap_shared_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio
from session_context_closeout import build_closeout_report
from session_context_reports import build_resume_report, build_save_report, format_text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persist or restore Forge session context from durable artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    save_parser = subparsers.add_parser("save", help="Persist the current task context into .brain/session.json")
    save_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    save_parser.add_argument("--feature", default="", help="Optional feature or workstream label")
    save_parser.add_argument("--task", default="", help="Optional task label")
    save_parser.add_argument("--status", default="", help="Optional task status")
    save_parser.add_argument("--file", action="append", default=[], help="Relevant file path. Repeatable.")
    save_parser.add_argument("--pending", action="append", default=[], help="Pending task. Repeatable.")
    save_parser.add_argument("--verification", action="append", default=[], help="Verification already run. Repeatable.")
    save_parser.add_argument("--decision", action="append", default=[], help="Important decision to persist. Repeatable.")
    save_parser.add_argument("--risk", action="append", default=[], help="Residual risk or blocker. Repeatable.")
    save_parser.add_argument("--blocker", action="append", default=[], help="Active blocker to preserve. Repeatable.")
    save_parser.add_argument("--next-step", default="", help="Optional best next step to pin into pending tasks")
    save_parser.add_argument("--write-handover", action="store_true", help="Also refresh .brain/handover.md")
    save_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    closeout_parser = subparsers.add_parser("closeout", help="Selectively persist durable task closeout context")
    closeout_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    closeout_parser.add_argument("--task", default="", help="Optional task label")
    closeout_parser.add_argument("--status", default="", help="Optional task status")
    closeout_parser.add_argument("--file", action="append", default=[], help="Relevant file path. Repeatable.")
    closeout_parser.add_argument("--pending", action="append", default=[], help="Pending task. Repeatable.")
    closeout_parser.add_argument("--verification", action="append", default=[], help="Verification already run. Repeatable.")
    closeout_parser.add_argument("--risk", action="append", default=[], help="Residual risk. Repeatable.")
    closeout_parser.add_argument("--blocker", action="append", default=[], help="Active blocker. Repeatable.")
    closeout_parser.add_argument("--decision", action="append", default=[], help="Durable decision summary. Repeatable.")
    closeout_parser.add_argument("--learning", action="append", default=[], help="Durable learning summary. Repeatable.")
    closeout_parser.add_argument("--evidence", action="append", default=[], help="Evidence for decision or learning entries. Repeatable.")
    closeout_parser.add_argument("--tag", action="append", default=[], help="Decision or learning tag. Repeatable.")
    closeout_parser.add_argument("--write-handover", action="store_true", help="Force refresh .brain/handover.md")
    closeout_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    resume_parser = subparsers.add_parser("resume", help="Restore context from repo state and persisted session artifacts")
    resume_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    resume_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    return parser


def main() -> int:
    configure_stdio()
    args = _parser().parse_args()
    workspace = args.workspace.resolve()
    if args.command == "save":
        report = build_save_report(workspace, args)
    elif args.command == "closeout":
        report = build_closeout_report(workspace, args)
    else:
        report = build_resume_report(workspace)

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
