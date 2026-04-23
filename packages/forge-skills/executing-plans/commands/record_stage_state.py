from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


VALID_STAGE_STATUSES = ("pending", "required", "active", "completed", "skipped", "blocked")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_report(args: argparse.Namespace) -> dict:
    if args.stage_status == "skipped" and not args.skip_reason:
        raise ValueError("Skipped stage-state requires --skip-reason.")
    if args.stage_status != "skipped" and not args.activation_reason:
        raise ValueError("Non-skipped stage-state requires --activation-reason.")
    if args.next_stage_override and args.next_stage_override == args.stage_name:
        raise ValueError("next_stage_override must differ from stage_name.")
    return {
        "recorded_at": _now_iso(),
        "project": args.project_name,
        "workspace": str(args.workspace.resolve()),
        "profile": args.profile or None,
        "intent": args.intent or None,
        "current_stage": args.stage_name,
        "required_stage_chain": args.required_stage,
        "stage_name": args.stage_name,
        "stage_status": args.stage_status,
        "activation_reason": args.activation_reason or None,
        "skip_reason": args.skip_reason or None,
        "artifact_refs": args.artifact_ref,
        "evidence_refs": args.evidence_ref,
        "decision": args.decision or None,
        "disposition": args.disposition or None,
        "target": args.target or None,
        "release_artifact_id": args.release_artifact_id or None,
        "post_deploy_verification": args.post_deploy_verification,
        "rollback_path": args.rollback_path or None,
        "next_stage_override": args.next_stage_override or None,
        "expected_previous_stage": args.expected_previous_stage or None,
        "transition_id": args.transition_id or None,
        "summary": args.summary,
        "notes": args.note,
        "next_actions": args.next_action,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Stage State",
        f"- Project: {report['project']}",
        f"- Stage: {report['stage_name']}",
        f"- Status: {report['stage_status']}",
        f"- Summary: {report['summary']}",
    ]
    for key, label in (
        ("activation_reason", "Activation reason"),
        ("skip_reason", "Skip reason"),
        ("decision", "Decision"),
        ("disposition", "Disposition"),
        ("target", "Target"),
        ("release_artifact_id", "Release artifact id"),
        ("rollback_path", "Rollback path"),
        ("next_stage_override", "Next stage override"),
        ("expected_previous_stage", "Expected previous stage"),
        ("transition_id", "Transition id"),
    ):
        value = report.get(key)
        if value:
            lines.append(f"- {label}: {value}")
    for label, items in (
        ("Artifact refs", report.get("artifact_refs", [])),
        ("Evidence refs", report.get("evidence_refs", [])),
        ("Post-deploy verification", report.get("post_deploy_verification", [])),
        ("Notes", report.get("notes", [])),
        ("Next actions", report.get("next_actions", [])),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
    return "\n".join(lines)


def persist_stage_report(
    report: dict,
    output_dir: str | None,
    *,
    artifact_kind: str = "stage-state",
    workflow_kind: str = "stage-state",
    stem_label: str | None = None,
    formatter=format_text,
) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, artifact_kind) / slugify(report["project"])
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stem_source = stem_label or report.get("summary") or report.get("stage_name") or "stage-state"
    stem = f"{timestamp_slug()}-{slugify(str(stem_source))[:48]}"
    latest_json = artifact_dir / "latest.json"
    latest_md = artifact_dir / "latest.md"
    json_path = history_dir / f"{stem}.json"
    md_path = history_dir / f"{stem}.md"
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    latest_json.write_text(payload, encoding="utf-8")
    json_path.write_text(payload, encoding="utf-8")
    text = formatter(report)
    latest_md.write_text(text, encoding="utf-8")
    md_path.write_text(text, encoding="utf-8")
    record_workflow_event(workflow_kind, report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record a canonical workflow stage-state entry.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name")
    parser.add_argument("--profile", default="", help="Optional operating profile")
    parser.add_argument("--intent", default="", help="Optional routed intent")
    parser.add_argument("--required-stage", action="append", default=[], help="Required stage in order. Repeatable.")
    parser.add_argument("--stage-name", required=True, help="Canonical stage name")
    parser.add_argument("--stage-status", choices=VALID_STAGE_STATUSES, required=True, help="Canonical stage status")
    parser.add_argument("--activation-reason", default="", help="Activation reason when the stage is not skipped")
    parser.add_argument("--skip-reason", default="", help="Skip reason when the stage is skipped")
    parser.add_argument("--artifact-ref", action="append", default=[], help="Artifact reference. Repeatable.")
    parser.add_argument("--evidence-ref", action="append", default=[], help="Evidence reference. Repeatable.")
    parser.add_argument("--decision", default="", help="Optional decision field")
    parser.add_argument("--disposition", default="", help="Optional disposition field")
    parser.add_argument("--target", default="", help="Optional target identity")
    parser.add_argument("--release-artifact-id", default="", help="Optional release or artifact id")
    parser.add_argument("--post-deploy-verification", action="append", default=[], help="Post-deploy verification reference. Repeatable.")
    parser.add_argument("--rollback-path", default="", help="Rollback path for deploy recovery")
    parser.add_argument("--next-stage-override", default="", help="Explicit next stage when not using the happy path")
    parser.add_argument("--expected-previous-stage", default="", help="Reject the write unless the current stage matches")
    parser.add_argument("--transition-id", default="", help="Explicit transition id")
    parser.add_argument("--summary", required=True, help="Human summary of the stage event")
    parser.add_argument("--note", action="append", default=[], help="Supporting note. Repeatable.")
    parser.add_argument("--next-action", action="append", default=[], help="Next action. Repeatable.")
    parser.add_argument("--persist", action="store_true", help="Persist stage state")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
        if args.persist:
            json_path, md_path = persist_stage_report(report, args.output_dir or str(args.workspace.resolve()))
            report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Stage State", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
