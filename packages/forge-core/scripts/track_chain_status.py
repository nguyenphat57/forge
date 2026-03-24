from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug


VALID_STATUSES = ("active", "paused", "completed", "blocked")


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

    return {
        "chain": args.chain,
        "project": args.project_name,
        "status": args.status,
        "current_stage": args.current_stage,
        "completed_stages": args.completed_stage,
        "next_stages": args.next_stage,
        "active_skills": args.active_skill,
        "active_lanes": args.active_lane,
        "lane_model_assignments": parse_lane_model_assignments(args.lane_model),
        "blockers": args.blocker,
        "risks": args.risk,
        "gate_decision": args.gate_decision,
        "review_iteration": args.review_iteration,
        "max_review_iterations": args.max_review_iterations,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Chain Status",
        f"- Chain: {report['chain']}",
        f"- Project: {report['project']}",
        f"- Status: {report['status']}",
        f"- Current stage: {report['current_stage']}",
        f"- Gate decision: {report['gate_decision'] or '(none)'}",
        f"- Review iteration: {report['review_iteration']}/{report['max_review_iterations'] or '-'}",
    ]
    for label, items in (
        ("Completed stages", report["completed_stages"]),
        ("Next stages", report["next_stages"]),
        ("Active skills", report["active_skills"]),
        ("Active lanes", report["active_lanes"]),
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
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "chain-status") / slugify(report["project"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['chain'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Track long-running Forge chain status.")
    parser.add_argument("chain", help="Chain name or task flow summary")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name")
    parser.add_argument("--status", choices=VALID_STATUSES, default="active", help="Chain status")
    parser.add_argument("--current-stage", required=True, help="Current stage in the chain")
    parser.add_argument("--completed-stage", action="append", default=[], help="Completed stage. Repeatable.")
    parser.add_argument("--next-stage", action="append", default=[], help="Next stage. Repeatable.")
    parser.add_argument("--active-skill", action="append", default=[], help="Currently active skill. Repeatable.")
    parser.add_argument("--active-lane", action="append", default=[], help="Currently active lane. Repeatable.")
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
