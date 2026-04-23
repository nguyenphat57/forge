from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


VALID_MODES = ("single-track", "checkpoint-batch", "parallel-safe")
VALID_STATUSES = ("active", "completed", "blocked")
VALID_PACKET_MODES = ("standard", "fast-lane")
VALID_COMPLETION_STATES = (
    "in-progress",
    "ready-for-review",
    "ready-for-merge",
    "blocked-by-residual-risk",
)
VALID_LANES = ("navigator", "implementer", "quality-reviewer", "deploy-reviewer")
VALID_MODEL_TIERS = ("cheap", "standard", "capable")
VALID_HARNESS_STATES = ("auto", "yes", "no")
VALID_BROWSER_QA_CLASSIFICATIONS = ("not-needed", "optional-accelerator", "required-for-this-packet")
VALID_BROWSER_QA_STATUSES = ("not-needed", "pending", "active", "satisfied", "blocked")
VALID_MERGE_STRATEGIES = ("none", "merge-commit", "squash", "rebase", "ff-only")
VALID_OVERLAP_RISK_STATUSES = ("none", "low", "medium", "high", "blocked")
VALID_READINESS_STATES = ("pending", "ready", "blocked")
VALID_COMPLETION_GATES = ("incomplete", "review-ready", "merge-ready", "blocked")


def _list_arg(args: argparse.Namespace, *names: str) -> list[str]:
    for name in names:
        value = getattr(args, name, None)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def _string_arg(args: argparse.Namespace, *names: str) -> str | None:
    for name in names:
        value = getattr(args, name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalized_browser_status(classification: str, status: str | None) -> str:
    if isinstance(status, str) and status in VALID_BROWSER_QA_STATUSES:
        return status
    return "not-needed" if classification == "not-needed" else "pending"


def _normalized_packet_mode(args: argparse.Namespace) -> str:
    packet_mode = _string_arg(args, "packet_mode")
    if packet_mode in VALID_PACKET_MODES:
        return packet_mode
    if bool(getattr(args, "fast_lane", False)):
        return "fast-lane"
    return "standard"


def _completion_gate_from_state(completion_state: str, explicit_gate: str | None) -> str:
    if isinstance(explicit_gate, str) and explicit_gate in VALID_COMPLETION_GATES:
        return explicit_gate
    mapping = {
        "ready-for-review": "review-ready",
        "ready-for-merge": "merge-ready",
        "blocked-by-residual-risk": "blocked",
    }
    return mapping.get(completion_state, "incomplete")


def _validate_choice(value: str | None, valid_values: tuple[str, ...], *, field: str) -> str | None:
    if value is None:
        return None
    if value not in valid_values:
        raise ValueError(f"{field} must be one of: {', '.join(valid_values)}")
    return value


def build_report(args: argparse.Namespace) -> dict:
    source_of_truth = _list_arg(args, "source", "source_of_truth")
    scope_paths = _list_arg(args, "scope_path", "exact_files_or_paths_in_scope")
    owned_scope = _list_arg(args, "owned_scope", "owned_files_or_write_scope")
    baseline_proof = _list_arg(args, "baseline", "baseline_or_clean_start_proof")
    out_of_scope = _list_arg(args, "out_of_scope", "out_of_scope_for_this_slice")
    reopen_conditions = _list_arg(args, "reopen_if", "reopen_conditions")
    harness_available = getattr(args, "harness_available", "auto")
    red_proof = _list_arg(args, "red", "red_proof")
    verification_to_rerun = _list_arg(args, "verify_again", "verification_to_rerun")
    depends_on_packets = _list_arg(args, "depends_on_packet", "depends_on_packets")
    unblocks_packets = _list_arg(args, "unblock_packet", "unblocks_packets")
    write_scope_conflicts = _list_arg(args, "write_scope_conflict", "write_scope_conflicts")
    browser_qa_classification = _string_arg(args, "browser_qa_classification") or "not-needed"
    browser_qa_scope = _list_arg(args, "browser_qa_scope")
    browser_qa_status = _normalized_browser_status(
        browser_qa_classification,
        _string_arg(args, "browser_qa_status"),
    )
    packet_mode = _normalized_packet_mode(args)
    merge_target = _string_arg(args, "merge_target")
    merge_strategy = _validate_choice(
        _string_arg(args, "merge_strategy") or ("none" if not merge_target else "merge-commit"),
        VALID_MERGE_STRATEGIES,
        field="merge_strategy",
    )
    overlap_risk_status = _validate_choice(
        _string_arg(args, "overlap_risk_status") or ("medium" if write_scope_conflicts else "none"),
        VALID_OVERLAP_RISK_STATUSES,
        field="overlap_risk_status",
    )
    review_readiness = _validate_choice(
        _string_arg(args, "review_readiness") or ("ready" if args.completion_state in {"ready-for-review", "ready-for-merge"} else "pending"),
        VALID_READINESS_STATES,
        field="review_readiness",
    )
    merge_readiness = _validate_choice(
        _string_arg(args, "merge_readiness") or ("ready" if args.completion_state == "ready-for-merge" else "pending"),
        VALID_READINESS_STATES,
        field="merge_readiness",
    )
    completion_gate = _completion_gate_from_state(args.completion_state, _string_arg(args, "completion_gate"))
    packet_id = _string_arg(args, "packet_id") or slugify(args.task) or "packet"
    parent_packet = _string_arg(args, "parent_packet")
    goal = _string_arg(args, "goal") or args.task
    next_steps = _list_arg(args, "next_step", "next_steps")
    blockers = _list_arg(args, "blocker", "blockers")
    residual_risk = _list_arg(args, "risk", "residual_risk")
    done = _list_arg(args, "done")
    report = {
        "packet_id": packet_id,
        "parent_packet": parent_packet,
        "project": args.project_name,
        "label": args.task,
        "task": args.task,
        "goal": goal,
        "packet_mode": packet_mode,
        "mode": args.mode,
        "stage": args.stage,
        "current_stage": args.stage,
        "status": args.status,
        "completion_state": args.completion_state,
        "profile": getattr(args, "profile", None),
        "intent": getattr(args, "intent", None),
        "required_stage_chain": list(getattr(args, "required_stage", []) or []),
        "lane": args.lane,
        "model_tier": args.model_tier,
        "source_of_truth": source_of_truth,
        "exact_files_or_paths_in_scope": scope_paths,
        "scope_paths": scope_paths,
        "owned_files_or_write_scope": owned_scope,
        "depends_on_packets": depends_on_packets,
        "unblocks_packets": unblocks_packets,
        "merge_target": merge_target,
        "merge_strategy": merge_strategy,
        "overlap_risk_status": overlap_risk_status,
        "write_scope_conflicts": write_scope_conflicts,
        "review_readiness": review_readiness,
        "merge_readiness": merge_readiness,
        "completion_gate": completion_gate,
        "baseline_or_clean_start_proof": baseline_proof,
        "baseline_proof": baseline_proof,
        "out_of_scope_for_this_slice": out_of_scope,
        "out_of_scope": out_of_scope,
        "reopen_conditions": reopen_conditions,
        "harness_available": harness_available,
        "red_proof": red_proof,
        "proof_before_progress": args.proof,
        "verification_to_rerun": verification_to_rerun,
        "browser_qa_classification": browser_qa_classification,
        "browser_qa_scope": browser_qa_scope,
        "browser_qa_status": browser_qa_status,
        "done": done,
        "next_steps": next_steps,
        "next": next_steps,
        "blockers": blockers,
        "residual_risk": residual_risk,
        "risks": residual_risk,
    }

    if report["completion_state"] in {"ready-for-review", "ready-for-merge"} and report["blockers"]:
        raise ValueError("Ready states cannot include blockers. Use blocked-by-residual-risk or clear blockers first.")

    if report["completion_state"] == "ready-for-merge" and report["status"] == "blocked":
        raise ValueError("ready-for-merge cannot be combined with blocked status.")

    if report["completion_state"] in {"ready-for-review", "ready-for-merge"} and not report["proof_before_progress"]:
        raise ValueError("Ready states require at least one proof-before-progress item.")

    if report["completion_state"] in {"ready-for-review", "ready-for-merge"} and report["harness_available"] == "yes" and not report["red_proof"]:
        raise ValueError("Harness-backed ready states require persisted RED proof before progress.")

    if report["merge_strategy"] != "none" and not report["merge_target"]:
        raise ValueError("merge_strategy requires merge_target.")

    if report["merge_readiness"] == "ready" and report["review_readiness"] != "ready":
        raise ValueError("merge_readiness=ready requires review_readiness=ready.")

    if report["merge_readiness"] == "ready" and report["write_scope_conflicts"]:
        raise ValueError("merge_readiness=ready cannot include unresolved write_scope_conflicts.")

    if report["overlap_risk_status"] == "blocked" and report["completion_state"] in {"ready-for-review", "ready-for-merge"}:
        raise ValueError("Ready states cannot keep overlap_risk_status=blocked.")

    if report["completion_gate"] == "review-ready" and report["review_readiness"] != "ready":
        raise ValueError("completion_gate=review-ready requires review_readiness=ready.")

    if report["completion_gate"] == "merge-ready" and report["merge_readiness"] != "ready":
        raise ValueError("completion_gate=merge-ready requires merge_readiness=ready.")

    if report["packet_mode"] == "fast-lane":
        if report["mode"] != "single-track":
            raise ValueError("Fast lane packets must use mode=single-track.")
        if report["lane"] not in {None, "implementer"}:
            raise ValueError("Fast lane packets cannot dispatch multi-lane ownership.")
        if report["depends_on_packets"] or report["unblocks_packets"] or report["merge_target"]:
            raise ValueError("Fast lane packets cannot declare packet graph dependencies or merge targets.")
        required_fields = {
            "exact_files_or_paths_in_scope": report["exact_files_or_paths_in_scope"],
            "owned_files_or_write_scope": report["owned_files_or_write_scope"],
            "baseline_or_clean_start_proof": report["baseline_or_clean_start_proof"],
            "proof_before_progress": report["proof_before_progress"],
            "verification_to_rerun": report["verification_to_rerun"],
            "residual_risk": report["residual_risk"],
            "next_steps": report["next_steps"],
        }
        missing = [name for name, value in required_fields.items() if not value]
        if missing:
            raise ValueError(f"Fast lane requires explicit values for: {', '.join(missing)}.")

    return report


def format_text(report: dict) -> str:
    lines = [
        "Forge Execution Progress",
        f"- Task: {report['task']}",
        f"- Packet ID: {report['packet_id']}",
        f"- Packet mode: {report['packet_mode']}",
        f"- Parent packet: {report['parent_packet'] or '(none)'}",
        f"- Goal: {report['goal']}",
        f"- Project: {report['project']}",
        f"- Mode: {report['mode']}",
        f"- Stage: {report['current_stage']}",
        f"- Status: {report['status']}",
        f"- Completion state: {report['completion_state']}",
        f"- Lane: {report['lane'] or '(none)'}",
        f"- Model tier: {report['model_tier'] or '(none)'}",
        f"- Harness available: {report['harness_available']}",
        f"- Browser QA: {report['browser_qa_classification']} / {report['browser_qa_status']}",
    ]

    for label, items in (
        ("Source of truth", report["source_of_truth"]),
        ("Scope paths", report["exact_files_or_paths_in_scope"]),
        ("Owned write scope", report["owned_files_or_write_scope"]),
        ("Depends on packets", report["depends_on_packets"]),
        ("Unblocks packets", report["unblocks_packets"]),
        ("Write scope conflicts", report["write_scope_conflicts"]),
        ("Baseline proof", report["baseline_or_clean_start_proof"]),
        ("RED proof", report["red_proof"]),
        ("Proof before progress", report["proof_before_progress"]),
        ("Verification to rerun", report["verification_to_rerun"]),
        ("Browser QA scope", report["browser_qa_scope"]),
        ("Done", report["done"]),
        ("Next", report["next_steps"]),
        ("Blockers", report["blockers"]),
        ("Risks", report["residual_risk"]),
        ("Out of scope", report["out_of_scope_for_this_slice"]),
        ("Reopen conditions", report["reopen_conditions"]),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")

    lines.extend(
        [
            f"- Merge target: {report['merge_target'] or '(none)'}",
            f"- Merge strategy: {report['merge_strategy']}",
            f"- Overlap risk status: {report['overlap_risk_status']}",
            f"- Review readiness: {report['review_readiness']}",
            f"- Merge readiness: {report['merge_readiness']}",
            f"- Completion gate: {report['completion_gate']}",
        ]
    )

    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "execution-progress") / slugify(report["project"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['task'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    record_workflow_event("execution-progress", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Track execution checkpoints for long-running Forge build work.")
    parser.add_argument("task", help="Task summary")
    parser.add_argument("--mode", required=True, choices=VALID_MODES, help="Execution mode for this task")
    parser.add_argument("--stage", required=True, help="Current stage or checkpoint name")
    parser.add_argument("--status", default="active", choices=VALID_STATUSES, help="Current execution status")
    parser.add_argument(
        "--packet-mode",
        choices=VALID_PACKET_MODES,
        default="standard",
        help="Packet contract mode for this slice",
    )
    parser.add_argument("--fast-lane", action="store_true", help="Alias for --packet-mode fast-lane")
    parser.add_argument(
        "--completion-state",
        default="in-progress",
        choices=VALID_COMPLETION_STATES,
        help="Delivery state at this checkpoint",
    )
    parser.add_argument("--profile", default=None, help="Optional operating profile for workflow-state")
    parser.add_argument("--intent", default=None, help="Optional intent for workflow-state")
    parser.add_argument("--required-stage", action="append", default=[], help="Required stage in order. Repeatable.")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for artifact grouping")
    parser.add_argument("--lane", choices=VALID_LANES, default=None, help="Active execution lane for this checkpoint")
    parser.add_argument(
        "--model-tier",
        choices=VALID_MODEL_TIERS,
        default=None,
        help="Recommended model tier for the active lane",
    )
    parser.add_argument("--source", action="append", default=[], help="Source-of-truth artifact or note. Repeatable.")
    parser.add_argument("--scope-path", action="append", default=[], help="Exact file/path scope for the current slice. Repeatable.")
    parser.add_argument("--owned-scope", action="append", default=[], help="Owned write scope for the current slice. Repeatable.")
    parser.add_argument("--depends-on-packet", action="append", default=[], help="Upstream packet dependency. Repeatable.")
    parser.add_argument("--unblock-packet", action="append", default=[], help="Downstream packet this slice unblocks. Repeatable.")
    parser.add_argument("--packet-id", default=None, help="Canonical packet identifier")
    parser.add_argument("--parent-packet", default=None, help="Parent packet identifier")
    parser.add_argument("--goal", default=None, help="Explicit goal for this packet")
    parser.add_argument("--merge-target", default=None, help="Planned merge target for this packet")
    parser.add_argument(
        "--merge-strategy",
        choices=VALID_MERGE_STRATEGIES,
        default=None,
        help="Merge strategy for the packet merge point",
    )
    parser.add_argument(
        "--overlap-risk-status",
        choices=VALID_OVERLAP_RISK_STATUSES,
        default=None,
        help="Current overlap-risk state for write scopes",
    )
    parser.add_argument("--write-scope-conflict", action="append", default=[], help="Unresolved write-scope conflict note. Repeatable.")
    parser.add_argument(
        "--review-readiness",
        choices=VALID_READINESS_STATES,
        default=None,
        help="Review readiness state for the current packet",
    )
    parser.add_argument(
        "--merge-readiness",
        choices=VALID_READINESS_STATES,
        default=None,
        help="Merge readiness state for the current packet",
    )
    parser.add_argument(
        "--completion-gate",
        choices=VALID_COMPLETION_GATES,
        default=None,
        help="Completion gate for handoff visibility",
    )
    parser.add_argument("--baseline", action="append", default=[], help="Baseline or clean-start proof. Repeatable.")
    parser.add_argument("--out-of-scope", action="append", default=[], help="Known out-of-scope boundary. Repeatable.")
    parser.add_argument("--reopen-if", action="append", default=[], help="Condition that re-opens this slice. Repeatable.")
    parser.add_argument(
        "--harness-available",
        choices=VALID_HARNESS_STATES,
        default="auto",
        help="Whether a usable harness exists for this slice",
    )
    parser.add_argument("--red", action="append", default=[], help="Failing RED proof observed before implementation. Repeatable.")
    parser.add_argument("--proof", action="append", default=[], help="Proof-before-progress item. Repeatable.")
    parser.add_argument("--verify-again", action="append", default=[], help="Verification that must be rerun before handoff. Repeatable.")
    parser.add_argument(
        "--browser-qa-classification",
        choices=VALID_BROWSER_QA_CLASSIFICATIONS,
        default="not-needed",
        help="Whether browser QA is needed for this packet",
    )
    parser.add_argument("--browser-qa-scope", action="append", default=[], help="Browser QA scope note. Repeatable.")
    parser.add_argument(
        "--browser-qa-status",
        choices=VALID_BROWSER_QA_STATUSES,
        default=None,
        help="Current browser QA status for this packet",
    )
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
