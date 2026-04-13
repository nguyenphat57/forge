from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from record_stage_state import persist_stage_report


# DEPRECATED(state-machine-cutover): retained as a compatibility wrapper until the current tooling surface removes this shim explicitly.


VALID_STAGE_STATUSES = ("pending", "required", "active", "completed", "skipped", "blocked")
VALID_DECISION_STATES = ("direction-locked", "decision-blocked")


def build_report(args: argparse.Namespace) -> dict:
    if args.stage_status == "skipped" and not args.skip_reason:
        raise ValueError("Skipped direction state requires --skip-reason.")
    if args.stage_status != "skipped" and not args.activation_reason:
        raise ValueError("Non-skipped direction state requires --activation-reason.")
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": args.project_name,
        "workspace": str(args.workspace.resolve()),
        "profile": args.profile,
        "intent": args.intent,
        "current_stage": "brainstorm",
        "required_stage_chain": args.required_stage,
        "stage_name": "brainstorm",
        "stage_status": args.stage_status,
        "mode": args.mode,
        "decision_state": args.decision_state,
        "activation_reason": args.activation_reason or None,
        "skip_reason": args.skip_reason or None,
        "artifact": args.artifact or None,
        "summary": args.summary,
        "notes": args.note,
        "next_actions": args.next_action,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Direction State",
        f"- Project: {report['project']}",
        f"- Profile: {report['profile']}",
        f"- Intent: {report['intent']}",
        f"- Status: {report['stage_status']}",
        f"- Mode: {report['mode']}",
        f"- Decision state: {report['decision_state']}",
        f"- Summary: {report['summary']}",
    ]
    if report.get("activation_reason"):
        lines.append(f"- Activation reason: {report['activation_reason']}")
    if report.get("skip_reason"):
        lines.append(f"- Skip reason: {report['skip_reason']}")
    if report.get("artifact"):
        lines.append(f"- Artifact: {report['artifact']}")
    for label, items in (("Notes", report["notes"]), ("Next actions", report["next_actions"])):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    return persist_stage_report(
        report,
        output_dir,
        artifact_kind="direction",
        workflow_kind="direction-state",
        stem_label=report["summary"],
        formatter=format_text,
    )


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record persisted brainstorm direction state.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name")
    parser.add_argument("--profile", required=True, help="Operating profile")
    parser.add_argument("--intent", required=True, help="Intent this direction belongs to")
    parser.add_argument("--required-stage", action="append", default=[], help="Required stage in order. Repeatable.")
    parser.add_argument("--stage-status", choices=VALID_STAGE_STATUSES, required=True, help="Workflow stage status")
    parser.add_argument("--mode", choices=["discovery-lite", "discovery-full"], default="discovery-lite", help="Discovery mode used")
    parser.add_argument("--decision-state", choices=VALID_DECISION_STATES, required=True, help="Brainstorm end state")
    parser.add_argument("--activation-reason", default="", help="Activation reason when the stage is not skipped")
    parser.add_argument("--skip-reason", default="", help="Skip reason when the stage is skipped")
    parser.add_argument("--artifact", default="", help="Optional artifact path")
    parser.add_argument("--summary", required=True, help="Direction summary")
    parser.add_argument("--note", action="append", default=[], help="Supporting note. Repeatable.")
    parser.add_argument("--next-action", action="append", default=[], help="Next action. Repeatable.")
    parser.add_argument("--persist", action="store_true", help="Persist direction state")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Direction State", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir or str(args.workspace.resolve()))
        report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
