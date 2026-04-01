from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


VALID_STAGE_STATUSES = ("pending", "required", "active", "completed", "skipped", "blocked")
VALID_IMPACTS = ("supports", "neutral", "contradicts")
VALID_CONFIDENCE = ("low", "medium", "high")
VALID_FRICTION_CATEGORIES = ("regression", "confusion", "adoption-lag", "environment-issue")
VALID_RELEASE_ACTIONS = ("monitor", "follow-up-fix", "rollback", "re-run-readiness")


def build_report(args: argparse.Namespace) -> dict:
    if args.stage_status == "skipped" and not args.skip_reason:
        raise ValueError("Skipped adoption-check state requires --skip-reason.")
    if args.stage_status != "skipped" and not args.activation_reason:
        raise ValueError("Non-skipped adoption-check state requires --activation-reason.")
    if args.impact != "supports" and not (args.friction or args.next_action):
        raise ValueError("Neutral or contradictory adoption checks require friction details or a next action.")
    if args.friction_category and not args.friction:
        raise ValueError("Friction categories require at least one --friction entry.")
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": args.project_name,
        "workspace": str(args.workspace.resolve()),
        "profile": args.profile,
        "intent": args.intent,
        "current_stage": "adoption-check",
        "required_stage_chain": args.required_stage,
        "stage_name": "adoption-check",
        "stage_status": args.stage_status,
        "activation_reason": args.activation_reason or None,
        "skip_reason": args.skip_reason or None,
        "artifact": args.artifact or None,
        "target": args.target,
        "summary": args.summary,
        "impact": args.impact,
        "confidence": args.confidence,
        "signals": args.signal,
        "evidence_sources": args.evidence_source,
        "metrics": args.metric,
        "frictions": args.friction,
        "friction_categories": args.friction_category,
        "release_actions": args.release_action,
        "next_actions": args.next_action,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Adoption Check",
        f"- Project: {report['project']}",
        f"- Profile: {report['profile']}",
        f"- Intent: {report['intent']}",
        f"- Stage status: {report['stage_status']}",
        f"- Target: {report['target']}",
        f"- Summary: {report['summary']}",
        f"- Impact on readiness: {report['impact']}",
        f"- Confidence: {report['confidence']}",
    ]
    if report.get("activation_reason"):
        lines.append(f"- Activation reason: {report['activation_reason']}")
    if report.get("skip_reason"):
        lines.append(f"- Skip reason: {report['skip_reason']}")
    if report.get("artifact"):
        lines.append(f"- Artifact: {report['artifact']}")
    for label, items in (
        ("Signals", report["signals"]),
        ("Evidence sources", report["evidence_sources"]),
        ("Metrics", report["metrics"]),
        ("Frictions", report["frictions"]),
        ("Friction categories", report["friction_categories"]),
        ("Release actions", report["release_actions"]),
        ("Next actions", report["next_actions"]),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "adoption-check") / slugify(report["project"])
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['summary'])[:48]}"
    latest_json = artifact_dir / "latest.json"
    latest_md = artifact_dir / "latest.md"
    json_path = history_dir / f"{stem}.json"
    md_path = history_dir / f"{stem}.md"
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    latest_json.write_text(payload, encoding="utf-8")
    json_path.write_text(payload, encoding="utf-8")
    text = format_text(report)
    latest_md.write_text(text, encoding="utf-8")
    md_path.write_text(text, encoding="utf-8")
    record_workflow_event("adoption-check", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record persisted adoption-check stage state.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name")
    parser.add_argument("--profile", required=True, help="Operating profile")
    parser.add_argument("--intent", required=True, help="Intent this stage belongs to")
    parser.add_argument("--required-stage", action="append", default=[], help="Required stage in order. Repeatable.")
    parser.add_argument("--stage-status", choices=VALID_STAGE_STATUSES, required=True, help="Workflow stage status")
    parser.add_argument("--activation-reason", default="", help="Activation reason when the stage is not skipped")
    parser.add_argument("--skip-reason", default="", help="Skip reason when the stage is skipped")
    parser.add_argument("--artifact", default="", help="Optional artifact path")
    parser.add_argument("--target", required=True, help="Target environment or audience")
    parser.add_argument("--summary", required=True, help="Adoption summary")
    parser.add_argument("--impact", choices=VALID_IMPACTS, default="supports", help="How the signal affects release readiness")
    parser.add_argument("--confidence", choices=VALID_CONFIDENCE, default="medium", help="Confidence in the recorded signal")
    parser.add_argument("--signal", action="append", default=[], help="Observed signal. Repeatable.")
    parser.add_argument("--evidence-source", action="append", default=[], help="Evidence source backing the signal. Repeatable.")
    parser.add_argument("--metric", action="append", default=[], help="Concrete metric or checkpoint. Repeatable.")
    parser.add_argument("--friction", action="append", default=[], help="Observed friction or early regression. Repeatable.")
    parser.add_argument(
        "--friction-category",
        action="append",
        default=[],
        choices=VALID_FRICTION_CATEGORIES,
        help="Bounded friction category. Repeatable.",
    )
    parser.add_argument(
        "--release-action",
        action="append",
        default=[],
        choices=VALID_RELEASE_ACTIONS,
        help="Bounded Forge release-tail action such as monitor, rollback, or re-run-readiness. Repeatable.",
    )
    parser.add_argument("--next-action", action="append", default=[], help="Next action. Repeatable.")
    parser.add_argument("--persist", action="store_true", help="Persist adoption-check state")
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
            print("\n".join(["Forge Adoption Check", "- Status: FAIL", f"- Error: {exc}"]))
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
