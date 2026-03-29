from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


VALID_DISPOSITIONS = ("ready-for-merge", "changes-required", "blocked-by-residual-risk")
VALID_REVIEW_KINDS = ("quality-pass", "spec-compliance", "merge-readiness", "release-review")


def build_report(args: argparse.Namespace) -> dict:
    findings = args.finding
    testing_gaps = args.testing_gap
    no_finding_rationale = args.no_finding_rationale.strip() if isinstance(args.no_finding_rationale, str) else ""

    if not findings and not testing_gaps and not no_finding_rationale:
        raise ValueError("Review state requires findings, testing gaps, or a no-finding rationale.")

    if args.disposition == "ready-for-merge":
        if findings or testing_gaps:
            raise ValueError("ready-for-merge review cannot carry findings or testing gaps.")
        if not no_finding_rationale:
            raise ValueError("ready-for-merge review requires --no-finding-rationale.")
        if not args.evidence:
            raise ValueError("ready-for-merge review requires fresh evidence.")

    if args.disposition == "changes-required" and not (findings or testing_gaps):
        raise ValueError("changes-required review must record at least one finding or testing gap.")

    if args.disposition == "blocked-by-residual-risk" and not (findings or testing_gaps):
        raise ValueError("blocked-by-residual-risk review must record the blocking issue.")

    status = {
        "ready-for-merge": "PASS",
        "changes-required": "WARN",
        "blocked-by-residual-risk": "FAIL",
    }[args.disposition]
    workspace = args.workspace.resolve()
    return {
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": args.project_name,
        "workspace": str(workspace),
        "scope": args.scope,
        "review_kind": args.review_kind,
        "disposition": args.disposition,
        "branch_state": args.branch_state,
        "findings": findings,
        "testing_gaps": testing_gaps,
        "evidence": args.evidence,
        "next_actions": args.next_action,
        "no_finding_rationale": no_finding_rationale or None,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Review State",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Project: {report['project']}",
        f"- Scope: {report['scope']}",
        f"- Review kind: {report['review_kind']}",
        f"- Disposition: {report['disposition']}",
        f"- Branch state: {report['branch_state']}",
    ]
    if report.get("no_finding_rationale"):
        lines.append(f"- No-finding rationale: {report['no_finding_rationale']}")
    for label, items in (
        ("Evidence", report["evidence"]),
        ("Findings", report["findings"]),
        ("Testing gaps", report["testing_gaps"]),
        ("Next actions", report["next_actions"]),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")
    artifacts = report.get("artifacts")
    if artifacts:
        lines.append("- Artifacts:")
        lines.append(f"  - JSON: {artifacts['json']}")
        lines.append(f"  - Markdown: {artifacts['markdown']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "reviews") / slugify(report["project"])
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['scope'])[:48]}"
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
    record_workflow_event("review-state", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record a persisted review disposition for the current Forge slice.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root the review applies to")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for grouping")
    parser.add_argument("--scope", required=True, help="Slice, packet, or review scope label")
    parser.add_argument("--review-kind", choices=VALID_REVIEW_KINDS, default="quality-pass", help="Review pass kind")
    parser.add_argument("--disposition", required=True, choices=VALID_DISPOSITIONS, help="Review disposition")
    parser.add_argument("--branch-state", required=True, help="Cleanliness or branch isolation note for the reviewed slice")
    parser.add_argument("--finding", action="append", default=[], help="Concrete review finding. Repeatable.")
    parser.add_argument("--testing-gap", action="append", default=[], help="Residual testing gap. Repeatable.")
    parser.add_argument("--evidence", action="append", default=[], help="Fresh evidence reviewed. Repeatable.")
    parser.add_argument("--next-action", action="append", default=[], help="Required follow-up action. Repeatable.")
    parser.add_argument("--no-finding-rationale", default="", help="Why the slice is clean when no findings were recorded")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the review state under .forge-artifacts/reviews")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Review State", "- Status: FAIL", f"- Error: {exc}"]))
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
