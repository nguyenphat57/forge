from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from quality_gate_artifacts import validate_supporting_artifacts
from workflow_state_support import record_workflow_event, resolve_workflow_state


VALID_PROFILES = (
    "standard",
    "release-critical",
    "migration-critical",
    "external-interface",
    "regression-recovery",
)
VALID_TARGET_CLAIMS = ("done", "ready-for-review", "ready-for-merge", "deploy")
VALID_DECISIONS = ("go", "conditional", "blocked")


def _workflow_profile(workflow_state: dict | None) -> str | None:
    if not isinstance(workflow_state, dict):
        return None
    profile = workflow_state.get("profile")
    return profile.strip() if isinstance(profile, str) and profile.strip() else None

def build_report(args: argparse.Namespace) -> dict:
    if not args.evidence:
        raise ValueError("Quality gate requires at least one fresh evidence item.")
    if args.decision in {"conditional", "blocked"} and not args.next_evidence:
        raise ValueError("Conditional or blocked decisions must name the next evidence needed.")
    workspace = args.workspace.resolve()
    workflow_state = resolve_workflow_state(workspace).get("state")
    operating_profile = _workflow_profile(workflow_state)
    if args.profile == "release-critical" and args.target_claim == "deploy" and args.decision == "conditional":
        raise ValueError("release-critical deploy gates cannot be conditional.")
    if operating_profile == "solo-public" and args.target_claim == "deploy" and args.decision == "conditional":
        raise ValueError("solo-public deploy gates cannot be conditional.")

    status = {"go": "PASS", "conditional": "WARN", "blocked": "FAIL"}[args.decision]
    process_artifacts, review_artifacts = validate_supporting_artifacts(args)
    return {
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": args.project_name,
        "workspace": str(workspace),
        "profile": args.profile,
        "operating_profile": operating_profile,
        "stage_name": "quality-gate",
        "stage_status": "completed" if args.decision == "go" else "blocked",
        "current_stage": "quality-gate",
        "target_claim": args.target_claim,
        "decision": args.decision,
        "evidence_read": args.evidence,
        "response": args.response,
        "why": args.why,
        "next_evidence": args.next_evidence,
        "risks": args.risk,
        "process_artifacts": process_artifacts,
        "review_artifacts": review_artifacts,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Quality Gate",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Project: {report['project']}",
        f"- Profile: {report['profile']}",
        f"- Operating profile: {report.get('operating_profile') or '(none)'}",
        f"- Target claim: {report['target_claim']}",
        f"- Decision: {report['decision']}",
        f"- Evidence response: {report['response']}",
        f"- Why: {report['why']}",
    ]
    for label, items in (("Evidence read", report["evidence_read"]), ("Next evidence needed", report["next_evidence"]), ("Risks", report["risks"])):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")
    for label, items in (("Process artifacts", report.get("process_artifacts", [])), ("Review artifacts", report.get("review_artifacts", []))):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item['kind']}: {item.get('summary') or '(none)'} | {item['path']}")
        else:
            lines.append(f"- {label}: (none)")
    artifacts = report.get("artifacts")
    if artifacts:
        lines.append("- Artifacts:")
        lines.append(f"  - JSON: {artifacts['json']}")
        lines.append(f"  - Markdown: {artifacts['markdown']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "quality-gates") / slugify(report["project"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{report['decision']}-{slugify(report['target_claim'])}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    record_workflow_event("quality-gate", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record an explicit Forge quality-gate decision from fresh evidence.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root the gate applies to")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for workflow-state grouping")
    parser.add_argument("--profile", required=True, choices=VALID_PROFILES, help="Quality-gate profile")
    parser.add_argument("--target-claim", required=True, choices=VALID_TARGET_CLAIMS, help="Claim being gated")
    parser.add_argument("--decision", required=True, choices=VALID_DECISIONS, help="Gate decision")
    parser.add_argument("--evidence", action="append", default=[], help="Fresh evidence item. Repeatable.")
    parser.add_argument("--response", required=True, help="Evidence response line that follows the gate contract")
    parser.add_argument("--why", required=True, help="Reason for the current gate decision")
    parser.add_argument("--next-evidence", action="append", default=[], help="Next evidence needed before the gate can improve")
    parser.add_argument("--risk", action="append", default=[], help="Residual risk note. Repeatable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the decision under .forge-artifacts/quality-gates")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Quality Gate", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
