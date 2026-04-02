from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


VALID_STATUSES = ("active", "paused", "completed", "blocked")
VALID_MERGE_STRATEGIES = ("none", "merge-commit", "squash", "rebase", "ff-only")
VALID_OVERLAP_RISK_STATUSES = ("none", "low", "medium", "high", "blocked")
VALID_READINESS_STATES = ("pending", "ready", "blocked")
VALID_COMPLETION_GATES = ("incomplete", "review-ready", "merge-ready", "blocked")


def _list_arg(args: argparse.Namespace, name: str) -> list[str]:
    value = getattr(args, name, None)
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def parse_lane_model_assignments(items: list[str]) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError("Lane model assignments must use the format lane=tier.")
        lane, tier = item.split("=", 1)
        lane = lane.strip()
        tier = tier.strip()
        if not lane or not tier:
            raise ValueError("Lane model assignments must include both lane and tier.")
        assignments[lane] = tier
    return assignments


def build_report(args: argparse.Namespace) -> dict:
    if args.review_iteration and args.max_review_iterations and args.review_iteration > args.max_review_iterations:
        raise ValueError("review_iteration cannot exceed max_review_iterations.")

    merge_target = getattr(args, "merge_target", None)
    merge_strategy = getattr(args, "merge_strategy", None) or ("none" if not merge_target else "merge-commit")
    overlap_risk_status = getattr(args, "overlap_risk_status", None) or ("medium" if _list_arg(args, "write_scope_overlap") else "none")
    review_readiness = getattr(args, "review_readiness", None) or ("ready" if _list_arg(args, "review_ready_packet") else "pending")
    merge_readiness = getattr(args, "merge_readiness", None) or ("ready" if _list_arg(args, "merge_ready_packet") else "pending")
    completion_gate = getattr(args, "completion_gate", None) or (
        "merge-ready"
        if merge_readiness == "ready"
        else "review-ready"
        if review_readiness == "ready"
        else "blocked"
        if args.status == "blocked" or args.gate_decision == "blocked"
        else "incomplete"
    )

    report = {
        "chain": args.chain,
        "project": args.project_name,
        "profile": getattr(args, "profile", None),
        "intent": getattr(args, "intent", None),
        "status": args.status,
        "current_stage": args.current_stage,
        "required_stage_chain": list(getattr(args, "required_stage", []) or []),
        "completed_stages": args.completed_stage,
        "next_stages": args.next_stage,
        "active_skills": args.active_skill,
        "active_lanes": args.active_lane,
        "lane_model_assignments": parse_lane_model_assignments(args.lane_model),
        "active_packets": _list_arg(args, "active_packet"),
        "blocked_packets": _list_arg(args, "blocked_packet"),
        "review_ready_packets": _list_arg(args, "review_ready_packet"),
        "merge_ready_packets": _list_arg(args, "merge_ready_packet"),
        "next_merge_point": getattr(args, "next_merge_point", None),
        "merge_target": merge_target,
        "merge_strategy": merge_strategy,
        "overlap_risk_status": overlap_risk_status,
        "review_readiness": review_readiness,
        "merge_readiness": merge_readiness,
        "completion_gate": completion_gate,
        "browser_qa_pending": _list_arg(args, "browser_qa_pending"),
        "write_scope_overlaps": _list_arg(args, "write_scope_overlap"),
        "sequential_reasons": _list_arg(args, "sequential_reason"),
        "blockers": args.blocker,
        "risks": args.risk,
        "gate_decision": args.gate_decision,
        "review_iteration": args.review_iteration,
        "max_review_iterations": args.max_review_iterations,
    }
    if report["merge_strategy"] != "none" and not report["merge_target"]:
        raise ValueError("merge_strategy requires merge_target.")
    if report["merge_readiness"] == "ready" and report["review_readiness"] != "ready":
        raise ValueError("merge_readiness=ready requires review_readiness=ready.")
    if report["merge_readiness"] == "ready" and report["write_scope_overlaps"]:
        raise ValueError("merge_readiness=ready cannot keep unresolved write_scope_overlaps.")
    if report["completion_gate"] == "review-ready" and report["review_readiness"] != "ready":
        raise ValueError("completion_gate=review-ready requires review_readiness=ready.")
    if report["completion_gate"] == "merge-ready" and report["merge_readiness"] != "ready":
        raise ValueError("completion_gate=merge-ready requires merge_readiness=ready.")
    if report["overlap_risk_status"] == "blocked" and report["completion_gate"] in {"review-ready", "merge-ready"}:
        raise ValueError("overlap_risk_status=blocked cannot be combined with ready completion gates.")
    return report


def format_text(report: dict) -> str:
    lines = [
        "Forge Chain Status",
        f"- Chain: {report['chain']}",
        f"- Project: {report['project']}",
        f"- Status: {report['status']}",
        f"- Current stage: {report['current_stage']}",
        f"- Gate decision: {report['gate_decision'] or '(none)'}",
        f"- Review iteration: {report['review_iteration']}/{report['max_review_iterations'] or '-'}",
        f"- Merge target: {report['merge_target'] or '(none)'}",
        f"- Merge strategy: {report['merge_strategy']}",
        f"- Overlap risk status: {report['overlap_risk_status']}",
        f"- Review readiness: {report['review_readiness']}",
        f"- Merge readiness: {report['merge_readiness']}",
        f"- Completion gate: {report['completion_gate']}",
    ]
    for label, items in (
        ("Completed stages", report["completed_stages"]),
        ("Next stages", report["next_stages"]),
        ("Active skills", report["active_skills"]),
        ("Active lanes", report["active_lanes"]),
        ("Active packets", report["active_packets"]),
        ("Blocked packets", report["blocked_packets"]),
        ("Review-ready packets", report["review_ready_packets"]),
        ("Merge-ready packets", report["merge_ready_packets"]),
        ("Browser QA pending", report["browser_qa_pending"]),
        ("Write-scope overlaps", report["write_scope_overlaps"]),
        ("Sequential reasons", report["sequential_reasons"]),
        ("Blockers", report["blockers"]),
        ("Risks", report["risks"]),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")

    if report["lane_model_assignments"]:
        lines.append("- Lane model assignments:")
        for lane, tier in report["lane_model_assignments"].items():
            lines.append(f"  - {lane}: {tier}")
    else:
        lines.append("- Lane model assignments: (none)")
    lines.append(f"- Next merge point: {report['next_merge_point'] or '(none)'}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "chain-status") / slugify(report["project"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['chain'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    record_workflow_event("chain-status", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Track long-running Forge chain status.")
    parser.add_argument("chain", help="Chain name or task flow summary")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name")
    parser.add_argument("--status", choices=VALID_STATUSES, default="active", help="Chain status")
    parser.add_argument("--current-stage", required=True, help="Current stage in the chain")
    parser.add_argument("--profile", default=None, help="Optional operating profile for workflow-state")
    parser.add_argument("--intent", default=None, help="Optional intent for workflow-state")
    parser.add_argument("--required-stage", action="append", default=[], help="Required stage in order. Repeatable.")
    parser.add_argument("--completed-stage", action="append", default=[], help="Completed stage. Repeatable.")
    parser.add_argument("--next-stage", action="append", default=[], help="Next stage. Repeatable.")
    parser.add_argument("--active-skill", action="append", default=[], help="Currently active skill. Repeatable.")
    parser.add_argument("--active-lane", action="append", default=[], help="Currently active lane. Repeatable.")
    parser.add_argument("--active-packet", action="append", default=[], help="Active packet identifier. Repeatable.")
    parser.add_argument("--blocked-packet", action="append", default=[], help="Blocked packet identifier. Repeatable.")
    parser.add_argument("--review-ready-packet", action="append", default=[], help="Review-ready packet identifier. Repeatable.")
    parser.add_argument("--merge-ready-packet", action="append", default=[], help="Merge-ready packet identifier. Repeatable.")
    parser.add_argument("--next-merge-point", default=None, help="Next merge point for active packets")
    parser.add_argument("--merge-target", default=None, help="Merge target label for the active chain")
    parser.add_argument(
        "--merge-strategy",
        choices=VALID_MERGE_STRATEGIES,
        default=None,
        help="Merge strategy used at the next merge point",
    )
    parser.add_argument(
        "--overlap-risk-status",
        choices=VALID_OVERLAP_RISK_STATUSES,
        default=None,
        help="Current overlap-risk state for active packet scopes",
    )
    parser.add_argument(
        "--review-readiness",
        choices=VALID_READINESS_STATES,
        default=None,
        help="Review readiness state for the chain",
    )
    parser.add_argument(
        "--merge-readiness",
        choices=VALID_READINESS_STATES,
        default=None,
        help="Merge readiness state for the chain",
    )
    parser.add_argument(
        "--completion-gate",
        choices=VALID_COMPLETION_GATES,
        default=None,
        help="Completion gate visibility for the chain",
    )
    parser.add_argument("--browser-qa-pending", action="append", default=[], help="Packet awaiting browser QA proof. Repeatable.")
    parser.add_argument("--write-scope-overlap", action="append", default=[], help="Write-scope overlap note. Repeatable.")
    parser.add_argument("--sequential-reason", action="append", default=[], help="Why the chain remains sequential. Repeatable.")
    parser.add_argument(
        "--lane-model",
        action="append",
        default=[],
        help="Lane model assignment using lane=tier. Repeatable.",
    )
    parser.add_argument("--blocker", action="append", default=[], help="Blocker. Repeatable.")
    parser.add_argument("--risk", action="append", default=[], help="Risk. Repeatable.")
    parser.add_argument("--gate-decision", choices=["go", "conditional", "blocked"], default=None, help="Optional latest gate decision")
    parser.add_argument("--review-iteration", type=int, default=0, help="Current spec/review iteration if applicable")
    parser.add_argument("--max-review-iterations", type=int, default=0, help="Maximum allowed spec/review iterations")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist under .forge-artifacts/chain-status")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted chain status:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
