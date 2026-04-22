from __future__ import annotations

from functools import lru_cache
from pathlib import Path


EVENT_ORDER = (
    "quality-gate",
    "review-state",
    "execution-progress",
    "run-report",
    "ui-progress",
    "chain-status",
)

STAGE_WORKFLOW_ALIASES = {
    "active-changes": "review",
    "blocked": "debug",
    "change-active": "session",
    "implementation": "build",
    "implement": "build",
    "integration": "build",
    "planned": "plan",
    "release-check": "test",
    "release-checks": "test",
    "review-ready": "review",
    "session-active": "session",
    "unscoped": "plan",
}

WORKFLOW_HINT_MARKERS = (
    ("debug", ("debug", "triage", "investigat", "repro", "fix", "failure")),
    ("review", ("review", "handoff", "signoff")),
    ("quality-gate", ("gate",)),
    ("test", ("test", "verify", "verification", "check", "smoke", "qa", "assert")),
    ("plan", ("plan", "slice", "scope", "bounded")),
    ("build", ("build", "implement", "integration", "migrat", "refactor", "coding", "develop")),
    ("session", ("session",)),
)


def as_string_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def combine_unique(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for item in group:
            if item in seen:
                continue
            seen.add(item)
            values.append(item)
    return values


def _packet_suffix(entry: dict | None) -> str:
    if not isinstance(entry, dict):
        return ""
    packet_id = entry.get("packet_id")
    return f" [{packet_id}]" if isinstance(packet_id, str) and packet_id.strip() else ""


def _packet_label(entry: dict | None) -> str | None:
    if not isinstance(entry, dict):
        return None
    label = entry.get("label")
    return label if isinstance(label, str) and label.strip() else None


def _gate_workflow(target_claim: str) -> str:
    return "deploy" if target_claim == "deploy" else "review"


@lru_cache(maxsize=1)
def _known_workflow_names() -> set[str]:
    workflow_root = Path(__file__).resolve().parents[1] / "workflows"
    if not workflow_root.exists():
        return set()
    return {candidate.stem.casefold() for candidate in workflow_root.rglob("*.md")}


def workflow_hint_for_stage(stage: str | None, *, default: str) -> str:
    known = _known_workflow_names()
    normalized_default = default.casefold()
    if normalized_default not in known:
        normalized_default = "session" if "session" in known else default
    if not isinstance(stage, str) or not stage.strip():
        return normalized_default

    lowered = stage.strip().casefold()
    if lowered in known:
        return lowered

    alias = STAGE_WORKFLOW_ALIASES.get(lowered)
    if isinstance(alias, str) and alias in known:
        return alias

    for workflow, markers in WORKFLOW_HINT_MARKERS:
        if workflow not in known:
            continue
        if any(marker in lowered for marker in markers):
            return workflow
    return normalized_default


def _route_preview_follow_on_stages(entry: dict | None) -> list[str]:
    if not isinstance(entry, dict):
        return []
    required_stage_chain = as_string_list(entry.get("required_stage_chain"))
    current_stage = entry.get("current_stage")
    if isinstance(current_stage, str) and current_stage in required_stage_chain:
        return required_stage_chain[required_stage_chain.index(current_stage) + 1 :]
    return required_stage_chain


def _route_preview_summary(entry: dict | None) -> dict | None:
    if not isinstance(entry, dict):
        return None
    current_stage = entry.get("current_stage")
    if not isinstance(current_stage, str) or not current_stage.strip():
        current_stage = "plan"
    follow_on = _route_preview_follow_on_stages(entry)
    alternatives: list[str] = []
    if follow_on:
        alternatives.append(f"After '{current_stage}', continue into '{follow_on[0]}'.")
    if len(follow_on) > 1:
        alternatives.append(f"Keep the remaining recorded chain in order: {', '.join(follow_on[1:3])}.")
    return {
        "status": "active",
        "primary_kind": "route-preview",
        "current_focus": f"Recorded workflow stage: {current_stage}",
        "current_stage": current_stage,
        "suggested_workflow": workflow_hint_for_stage(current_stage, default="plan"),
        "recommended_action": f"Resume the recorded workflow stage '{current_stage}' before opening new scope.",
        "alternatives": alternatives,
    }


def summarize_workflow_state(
    latest_chain: dict | None,
    latest_execution: dict | None,
    latest_ui: dict | None,
    latest_run: dict | None,
    latest_gate: dict | None,
    latest_review: dict | None,
    latest_route_preview: dict | None = None,
    *,
    preferred_kind: str | None = None,
) -> dict:
    if not any((latest_chain, latest_execution, latest_ui, latest_run, latest_gate, latest_review)):
        route_preview_summary = _route_preview_summary(latest_route_preview)
        if route_preview_summary is not None:
            return route_preview_summary

    blockers = combine_unique(as_string_list((latest_execution or {}).get("blockers")), as_string_list((latest_chain or {}).get("blockers")))
    risks = combine_unique(
        as_string_list((latest_review or {}).get("testing_gaps")),
        as_string_list((latest_review or {}).get("findings")),
        as_string_list((latest_gate or {}).get("risks")),
        as_string_list((latest_execution or {}).get("residual_risk")),
        as_string_list((latest_execution or {}).get("risks")),
        as_string_list((latest_chain or {}).get("risks")),
    )
    next_steps = combine_unique(
        as_string_list((latest_review or {}).get("next_steps")),
        as_string_list((latest_gate or {}).get("next_evidence")),
        as_string_list((latest_execution or {}).get("next_steps")),
        as_string_list((latest_ui or {}).get("next_steps")),
        as_string_list((latest_chain or {}).get("next_steps")),
    )
    entries = {
        "quality-gate": latest_gate,
        "review-state": latest_review,
        "execution-progress": latest_execution,
        "run-report": latest_run,
        "ui-progress": latest_ui,
        "chain-status": latest_chain,
    }
    preferred_order = [preferred_kind] if preferred_kind in {"run-report", "quality-gate", "review-state"} else []
    ordered_kinds = [kind for kind in (*preferred_order, *EVENT_ORDER) if kind and kind in entries]
    seen: set[str] = set()
    for kind in ordered_kinds:
        if kind in seen:
            continue
        seen.add(kind)
        entry = entries.get(kind)
        if not entry:
            continue
        if kind == "quality-gate":
            decision = entry.get("decision")
            target_claim = entry.get("label", "claim")
            action = entry.get("why") or entry.get("response") or f"Re-open the gate for '{target_claim}'."
            if decision == "blocked":
                return {
                    "status": "blocked",
                    "primary_kind": kind,
                    "current_focus": f"Gate blocked: {target_claim}",
                    "current_stage": "quality-gate",
                    "suggested_workflow": "debug",
                    "recommended_action": f"Do not claim '{target_claim}' yet. Next evidence needed: {next_steps[0]}." if next_steps else f"Do not claim '{target_claim}' yet. Resolve the gate blocker: {action}",
                    "alternatives": next_steps[1:3] or risks[:1],
                }
            if decision == "conditional":
                return {
                    "status": "review-ready",
                    "primary_kind": kind,
                    "current_focus": f"Conditional gate: {target_claim}",
                    "current_stage": "quality-gate",
                    "suggested_workflow": "review",
                    "recommended_action": f"Address the mandatory follow-up before claiming '{target_claim}': {next_steps[0]}." if next_steps else f"Address the residual gate condition before claiming '{target_claim}': {action}",
                    "alternatives": next_steps[1:3] or risks[:1],
                }
            workflow = _gate_workflow(target_claim)
            approved_action = f"Proceed with the approved {workflow} step for '{target_claim}'." if workflow == "deploy" else f"Proceed with the approved handoff for '{target_claim}'."
            return {
                "status": "active",
                "primary_kind": kind,
                "current_focus": f"Gate approved: {target_claim}",
                "current_stage": "quality-gate",
                "suggested_workflow": workflow,
                "recommended_action": approved_action,
                "alternatives": risks[:1] or as_string_list(entry.get("evidence_read"))[:1],
            }
        if kind == "review-state":
            disposition = entry.get("disposition")
            review_items = combine_unique(
                as_string_list(entry.get("findings")),
                as_string_list(entry.get("testing_gaps")),
                as_string_list(entry.get("next_steps")),
            )
            if disposition in {"changes-required", "blocked-by-residual-risk"}:
                label = "Blocked review" if disposition == "blocked-by-residual-risk" else "Review follow-up"
                action = (
                    f"Address the review follow-up first: {review_items[0]}."
                    if review_items
                    else f"Address the review follow-up for '{entry['label']}' before advancing."
                )
                return {
                    "status": "blocked",
                    "primary_kind": kind,
                    "current_focus": f"{label}: {entry['label']}",
                    "current_stage": "review",
                    "suggested_workflow": "build",
                    "recommended_action": action,
                    "alternatives": review_items[1:3] or as_string_list(entry.get("evidence"))[:1],
                }
            alternatives = as_string_list(entry.get("evidence"))[:2]
            branch_state = entry.get("branch_state")
            if not alternatives and isinstance(branch_state, str) and branch_state.strip():
                alternatives = [f"Branch state: {branch_state.strip()}"]
            return {
                "status": "active",
                "primary_kind": kind,
                "current_focus": f"Review cleared: {entry['label']}",
                "current_stage": "review",
                "suggested_workflow": "quality-gate",
                "recommended_action": "Refresh the quality gate from the persisted review evidence before claiming merge readiness.",
                "alternatives": alternatives,
            }
        if kind == "execution-progress":
            packet_label = _packet_label(entry) or "Unnamed packet"
            packet_suffix = _packet_suffix(entry)
            packet_mode = entry.get("packet_mode") if isinstance(entry.get("packet_mode"), str) else "standard"
            completion_state = entry.get("completion_state")
            completion_gate = entry.get("completion_gate")
            browser_qa_status = entry.get("browser_qa_status")
            browser_qa_classification = entry.get("browser_qa_classification")
            depends_on_packets = as_string_list(entry.get("depends_on_packets"))
            unblocks_packets = as_string_list(entry.get("unblocks_packets"))
            write_scope_conflicts = as_string_list(entry.get("write_scope_conflicts"))
            merge_target = entry.get("merge_target")
            overlap_risk_status = entry.get("overlap_risk_status")
            review_readiness = entry.get("review_readiness")
            merge_readiness = entry.get("merge_readiness")
            latest_run_packet = (latest_run or {}).get("packet_id") if isinstance(latest_run, dict) else None
            stale_runtime_proof = (
                isinstance(latest_run_packet, str)
                and latest_run_packet.strip()
                and latest_run_packet != entry.get("packet_id")
                and browser_qa_classification in {"optional-accelerator", "required-for-this-packet"}
            )
            browser_pending = (
                browser_qa_classification in {"optional-accelerator", "required-for-this-packet"}
                and browser_qa_status in {"pending", "active", "blocked"}
            )
            active_packets = [entry.get("packet_id") or packet_label]
            browser_qa_pending = active_packets if browser_pending else []
            packet_focus_prefix = "Fast-lane packet" if packet_mode == "fast-lane" else "Build packet"

            if overlap_risk_status == "blocked" or (completion_gate == "blocked" and write_scope_conflicts):
                conflict_message = write_scope_conflicts[0] if write_scope_conflicts else "merge overlap is still blocked"
                return {
                    "status": "blocked",
                    "primary_kind": kind,
                    "current_focus": f"Blocked execution: {packet_label}{packet_suffix}",
                    "current_stage": entry["current_stage"],
                    "suggested_workflow": "debug",
                    "recommended_action": f"Resolve packet graph overlap before continuing: {conflict_message}.",
                    "alternatives": next_steps[:2],
                    "active_packets": active_packets,
                    "blocked_packets": active_packets,
                    "browser_qa_pending": browser_qa_pending,
                    "write_scope_conflicts": write_scope_conflicts,
                }

            if entry.get("status") == "blocked" or completion_state == "blocked-by-residual-risk" or blockers:
                blocked_action = f"Resolve the execution blocker first: {blockers[0] if blockers else packet_label}."
                return {
                    "status": "blocked",
                    "primary_kind": kind,
                    "current_focus": f"Blocked execution: {packet_label}{packet_suffix}",
                    "current_stage": entry["current_stage"],
                    "suggested_workflow": "debug",
                    "recommended_action": blocked_action,
                    "alternatives": next_steps[:2],
                    "active_packets": active_packets,
                    "blocked_packets": active_packets,
                    "browser_qa_pending": browser_qa_pending,
                }
            if completion_state in {"ready-for-review", "ready-for-merge"}:
                action = f"Run review and verification for '{packet_label}' before starting a new slice."
                if browser_pending:
                    action = f"Run review for '{packet_label}' after clearing the pending browser QA proof."
                if completion_state == "ready-for-merge" and isinstance(merge_target, str) and merge_target.strip():
                    action = f"{action} Merge target: {merge_target.strip()}."
                return {
                    "status": "review-ready",
                    "primary_kind": kind,
                    "current_focus": f"Review ready: {packet_label}{packet_suffix}",
                    "current_stage": entry["current_stage"],
                    "suggested_workflow": "review",
                    "recommended_action": action,
                    "alternatives": next_steps[:2] or risks[:1],
                    "active_packets": active_packets,
                    "review_ready_packets": active_packets,
                    "browser_qa_pending": browser_qa_pending,
                    "packet_mode": packet_mode,
                    "depends_on_packets": depends_on_packets,
                    "unblocks_packets": unblocks_packets,
                    "review_readiness": review_readiness,
                    "merge_readiness": merge_readiness,
                    "completion_gate": completion_gate,
                }
            action = (
                f"Resume packet '{entry['packet_id']}' and clear the pending browser QA proof before starting a new slice."
                if browser_pending and isinstance(entry.get("packet_id"), str) and entry.get("packet_id")
                else f"Continue '{packet_label}' with the next recorded step: {next_steps[0]}."
                if next_steps
                else f"Continue the active execution slice: {packet_label}."
            )
            if stale_runtime_proof:
                action = (
                    f"Recorded browser proof is stale for this packet. Re-run browser QA for '{entry.get('packet_id') or packet_label}' before continuing."
                )
            if packet_mode == "fast-lane" and not browser_pending:
                action = (
                    f"Continue fast-lane packet '{entry['packet_id']}' with the next recorded step: {next_steps[0]}."
                    if isinstance(entry.get("packet_id"), str) and entry.get("packet_id") and next_steps
                    else f"Continue fast-lane packet '{packet_label}' with explicit proof rerun."
                )
            alternatives = next_steps[1:3] or risks[:1]
            if packet_mode == "fast-lane":
                alternatives = combine_unique(
                    ["Escalate to standard packet mode if dependency or overlap risk appears."],
                    alternatives,
                )[:2]
            if stale_runtime_proof:
                alternatives = combine_unique(
                    alternatives,
                    ["If runtime resolution fails, follow the recorded runtime recovery guidance before retrying browser proof."],
                )[:2]
            if isinstance(merge_target, str) and merge_target.strip():
                alternatives = combine_unique(alternatives, [f"Next merge target: {merge_target.strip()}."])[:2]
            return {
                "status": "active",
                "primary_kind": kind,
                "current_focus": f"{packet_focus_prefix}: {packet_label}{packet_suffix}",
                "current_stage": entry["current_stage"],
                "suggested_workflow": workflow_hint_for_stage(entry.get("current_stage"), default="build"),
                "recommended_action": action,
                "alternatives": alternatives,
                "active_packets": active_packets,
                "browser_qa_pending": browser_qa_pending,
                "packet_mode": packet_mode,
                "depends_on_packets": depends_on_packets,
                "unblocks_packets": unblocks_packets,
                "merge_target": merge_target,
                "write_scope_conflicts": write_scope_conflicts,
                "review_readiness": review_readiness,
                "merge_readiness": merge_readiness,
                "completion_gate": completion_gate,
                "stale_runtime_proof": stale_runtime_proof,
            }
        if kind == "run-report":
            blocked = entry.get("state") in {"failed", "timed-out"}
            runtime_taxonomy = entry.get("runtime_health_taxonomy") or entry.get("runtime_failure_taxonomy")
            runtime_summary = entry.get("runtime_health_summary")
            runtime_doctor = entry.get("runtime_doctor_command")
            action = entry.get("recommended_action") or "Inspect the latest run result before moving on."
            alternatives = as_string_list(entry.get("warnings"))[:2] or next_steps[:1]
            if isinstance(runtime_taxonomy, str) and runtime_taxonomy in {"stale-registration", "runtime-missing", "runtime-invalid", "runtime-unresolvable"}:
                blocked = True
                action = (
                    f"Runtime health issue detected ({runtime_taxonomy}). "
                    + (
                        runtime_summary
                        if isinstance(runtime_summary, str) and runtime_summary.strip()
                        else "Resolve the runtime health issue before retrying."
                    )
                )
                if isinstance(runtime_doctor, str) and runtime_doctor.strip():
                    alternatives = combine_unique([f"Doctor command: {runtime_doctor.strip()}"], alternatives)[:2]
            return {
                "status": "blocked" if blocked else "active",
                "primary_kind": kind,
                "current_focus": f"Run {'failed' if blocked else 'result'}: {entry['label']}",
                "current_stage": entry.get("command_kind", "generic"),
                "suggested_workflow": workflow_hint_for_stage(
                    entry.get("suggested_workflow") or entry.get("current_stage"),
                    default="debug" if blocked else "test",
                ),
                "recommended_action": action,
                "alternatives": alternatives,
            }
        if kind == "ui-progress":
            stage = entry["current_stage"]
            if entry.get("status") == "blocked":
                notes = as_string_list(entry.get("notes"))
                return {
                    "status": "blocked",
                    "primary_kind": kind,
                    "current_focus": f"Blocked UI task: {entry['label']}",
                    "current_stage": stage,
                    "suggested_workflow": "debug",
                    "recommended_action": f"Resolve the active UI blocker first: {notes[0] if notes else entry['label']}.",
                    "alternatives": next_steps[:2],
                }
            if stage in {"responsive-a11y-review", "states-platform-review"}:
                return {
                    "status": "review-ready",
                    "primary_kind": kind,
                    "current_focus": f"UI review ready: {entry['label']}",
                    "current_stage": stage,
                    "suggested_workflow": "review",
                    "recommended_action": f"Run the {entry.get('mode', 'frontend')} review pass for '{entry['label']}' before starting a new design slice.",
                    "alternatives": next_steps[:2] or as_string_list(entry.get("notes"))[:1],
                }
            return {
                "status": "active",
                "primary_kind": kind,
                "current_focus": f"UI task: {entry['label']}",
                "current_stage": stage,
                "suggested_workflow": "session",
                "recommended_action": f"Advance UI task '{entry['label']}' to the next recorded stage: {next_steps[0]}." if next_steps else f"Continue the active UI task: {entry['label']}.",
                "alternatives": next_steps[1:3] or as_string_list(entry.get("notes"))[:1],
            }
        gate_decision = entry.get("gate_decision")
        active_packets = as_string_list(entry.get("active_packets"))
        blocked_packets = as_string_list(entry.get("blocked_packets"))
        review_ready_packets = as_string_list(entry.get("review_ready_packets"))
        merge_ready_packets = as_string_list(entry.get("merge_ready_packets"))
        browser_qa_pending = as_string_list(entry.get("browser_qa_pending"))
        write_scope_overlaps = as_string_list(entry.get("write_scope_overlaps"))
        overlap_risk_status = entry.get("overlap_risk_status")
        review_readiness = entry.get("review_readiness")
        merge_readiness = entry.get("merge_readiness")
        completion_gate = entry.get("completion_gate")
        next_merge_point = entry.get("next_merge_point")
        merge_target = entry.get("merge_target")
        if entry.get("status") == "blocked" or gate_decision == "blocked" or blockers:
            return {
                "status": "blocked",
                "primary_kind": kind,
                "current_focus": f"Blocked chain: {entry['label']}",
                "current_stage": entry["current_stage"],
                "suggested_workflow": "debug",
                "recommended_action": f"Resolve the chain blocker first: {blockers[0] if blockers else entry['label']}.",
                "alternatives": next_steps[:2],
            }
        if gate_decision == "conditional":
            return {
                "status": "review-ready",
                "primary_kind": kind,
                "current_focus": f"Gate review: {entry['label']}",
                "current_stage": entry["current_stage"],
                "suggested_workflow": "review",
                "recommended_action": f"Run the current gate/review pass for '{entry['label']}' before advancing stages.",
                "alternatives": next_steps[:2] or risks[:1],
            }
        if overlap_risk_status == "blocked" or (completion_gate == "blocked" and write_scope_overlaps):
            overlap_message = write_scope_overlaps[0] if write_scope_overlaps else "merge overlap risk is blocked"
            return {
                "status": "blocked",
                "primary_kind": kind,
                "current_focus": f"Blocked chain: {entry['label']}",
                "current_stage": entry["current_stage"],
                "suggested_workflow": "debug",
                "recommended_action": f"Resolve chain overlap risk before merge: {overlap_message}.",
                "alternatives": next_steps[:2] or risks[:1],
                "active_packets": active_packets,
                "blocked_packets": blocked_packets or active_packets,
                "write_scope_overlaps": write_scope_overlaps,
            }
        action = (
            f"Advance chain '{entry['label']}' to merge point '{next_merge_point}'."
            if isinstance(next_merge_point, str) and next_merge_point.strip()
            else f"Advance chain '{entry['label']}' to the next stage: {next_steps[0]}."
            if next_steps
            else f"Continue the active chain: {entry['label']}."
        )
        if browser_qa_pending:
            action = f"{action} Clear pending browser QA for: {', '.join(browser_qa_pending)}."
        if merge_readiness == "ready":
            target = merge_target if isinstance(merge_target, str) and merge_target.strip() else next_merge_point
            if isinstance(target, str) and target.strip():
                action = f"Chain is merge-ready. Route into merge target '{target.strip()}' with the recorded strategy."
        return {
            "status": "active",
            "primary_kind": kind,
            "current_focus": f"Chain: {entry['label']}",
            "current_stage": entry["current_stage"],
            "suggested_workflow": "session",
            "recommended_action": action,
            "alternatives": next_steps[1:3] or risks[:1],
            "active_packets": active_packets,
            "blocked_packets": blocked_packets,
            "review_ready_packets": review_ready_packets,
            "merge_ready_packets": merge_ready_packets,
            "browser_qa_pending": browser_qa_pending,
            "next_merge_point": next_merge_point,
            "merge_target": merge_target,
            "write_scope_overlaps": write_scope_overlaps,
            "overlap_risk_status": overlap_risk_status,
            "review_readiness": review_readiness,
            "merge_readiness": merge_readiness,
            "completion_gate": completion_gate,
        }
    return {
        "status": "empty",
        "primary_kind": None,
        "current_focus": "No workflow state recorded.",
        "current_stage": None,
        "suggested_workflow": "plan",
        "recommended_action": "Run `python scripts/verify_repo.py --profile fast` if repo health is unclear, then state one bounded slice so Forge can route directly.",
        "alternatives": [],
    }


def workflow_summary(workflow_state: dict | None) -> dict | None:
    if not isinstance(workflow_state, dict):
        return None
    summary = workflow_state.get("summary")
    return summary if isinstance(summary, dict) else None


def summary_text(summary: dict | None, key: str) -> str | None:
    if not isinstance(summary, dict):
        return None
    value = summary.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def summary_items(summary: dict | None, key: str) -> list[str]:
    if not isinstance(summary, dict):
        return []
    value = summary.get(key)
    return [item.strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []
