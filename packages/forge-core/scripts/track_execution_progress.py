from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug


VALID_MODES = ("single-track", "checkpoint-batch", "parallel-safe")
VALID_STATUSES = ("active", "completed", "blocked")
VALID_COMPLETION_STATES = (
    "in-progress",
    "ready-for-review",
    "ready-for-merge",
    "blocked-by-residual-risk",
)
VALID_LANES = ("navigator", "implementer", "spec-reviewer", "quality-reviewer", "deploy-reviewer")
VALID_MODEL_TIERS = ("cheap", "standard", "capable")


def build_report(args: argparse.Namespace) -> dict:
    report = {
        "task": args.task,
        "mode": args.mode,
        "stage": args.stage,
        "status": args.status,
        "completion_state": args.completion_state,
        "lane": args.lane,
        "model_tier": args.model_tier,
        "proof_before_progress": args.proof,
        "done": args.done,
        "next": args.next_step,
        "blockers": args.blocker,
        "risks": args.risk,
        "project": args.project_name,
    }

    if report["completion_state"] in {"ready-for-review", "ready-for-merge"} and report["blockers"]:
        raise ValueError("Ready states cannot include blockers. Use blocked-by-residual-risk or clear blockers first.")

    if report["completion_state"] == "ready-for-merge" and report["status"] == "blocked":
        raise ValueError("ready-for-merge cannot be combined with blocked status.")

    if report["completion_state"] in {"ready-for-review", "ready-for-merge"} and not report["proof_before_progress"]:
        raise ValueError("Ready states require at least one proof-before-progress item.")

    return report


def format_text(report: dict) -> str:
    lines = [
        "Forge Execution Progress",
        f"- Task: {report['task']}",
        f"- Project: {report['project']}",
        f"- Mode: {report['mode']}",
        f"- Stage: {report['stage']}",
        f"- Status: {report['status']}",
        f"- Completion state: {report['completion_state']}",
        f"- Lane: {report['lane'] or '(none)'}",
        f"- Model tier: {report['model_tier'] or '(none)'}",
    ]

    for label, items in (
        ("Proof before progress", report["proof_before_progress"]),
        ("Done", report["done"]),
        ("Next", report["next"]),
        ("Blockers", report["blockers"]),
        ("Risks", report["risks"]),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")

    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "execution-progress") / slugify(report["project"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['task'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Track execution checkpoints for long-running Forge build work.")
    parser.add_argument("task", help="Task summary")
    parser.add_argument("--mode", required=True, choices=VALID_MODES, help="Execution mode for this task")
    parser.add_argument("--stage", required=True, help="Current stage or checkpoint name")
    parser.add_argument("--status", default="active", choices=VALID_STATUSES, help="Current execution status")
    parser.add_argument(
        "--completion-state",
        default="in-progress",
        choices=VALID_COMPLETION_STATES,
        help="Delivery state at this checkpoint",
    )
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for artifact grouping")
    parser.add_argument("--lane", choices=VALID_LANES, default=None, help="Active execution lane for this checkpoint")
    parser.add_argument(
        "--model-tier",
        choices=VALID_MODEL_TIERS,
        default=None,
        help="Recommended model tier for the active lane",
    )
    parser.add_argument("--proof", action="append", default=[], help="Proof-before-progress item. Repeatable.")
    parser.add_argument("--done", action="append", default=[], help="Completed item. Repeatable.")
    parser.add_argument("--next", dest="next_step", action="append", default=[], help="Next item. Repeatable.")
    parser.add_argument("--blocker", action="append", default=[], help="Blocker or unresolved issue. Repeatable.")
    parser.add_argument("--risk", action="append", default=[], help="Residual risk. Repeatable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the checkpoint under .forge-artifacts/execution-progress")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args)

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted execution progress:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
