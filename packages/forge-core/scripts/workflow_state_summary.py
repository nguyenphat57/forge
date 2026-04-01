from __future__ import annotations


EVENT_ORDER = (
    "quality-gate",
    "review-state",
    "execution-progress",
    "run-report",
    "ui-progress",
    "chain-status",
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


def _gate_workflow(target_claim: str) -> str:
    return "deploy" if target_claim == "deploy" else "review"


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
        "suggested_workflow": current_stage,
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
            completion_state = entry.get("completion_state")
            if entry.get("status") == "blocked" or completion_state == "blocked-by-residual-risk" or blockers:
                return {
                    "status": "blocked",
                    "primary_kind": kind,
                    "current_focus": f"Blocked execution: {entry['label']}",
                    "current_stage": entry["current_stage"],
                    "suggested_workflow": "debug",
                    "recommended_action": f"Resolve the execution blocker first: {blockers[0] if blockers else entry['label']}.",
                    "alternatives": next_steps[:2],
                }
            if completion_state in {"ready-for-review", "ready-for-merge"}:
                return {
                    "status": "review-ready",
                    "primary_kind": kind,
                    "current_focus": f"Review ready: {entry['label']}",
                    "current_stage": entry["current_stage"],
                    "suggested_workflow": "review",
                    "recommended_action": f"Run review and verification for '{entry['label']}' before starting a new slice.",
                    "alternatives": next_steps[:2] or risks[:1],
                }
            return {
                "status": "active",
                "primary_kind": kind,
                "current_focus": f"Execution task: {entry['label']}",
                "current_stage": entry["current_stage"],
                "suggested_workflow": "session",
                "recommended_action": f"Continue '{entry['label']}' with the next recorded step: {next_steps[0]}." if next_steps else f"Continue the active execution slice: {entry['label']}.",
                "alternatives": next_steps[1:3] or risks[:1],
            }
        if kind == "run-report":
            blocked = entry.get("state") in {"failed", "timed-out"}
            return {
                "status": "blocked" if blocked else "active",
                "primary_kind": kind,
                "current_focus": f"Run {'failed' if blocked else 'result'}: {entry['label']}",
                "current_stage": entry.get("command_kind", "generic"),
                "suggested_workflow": entry.get("suggested_workflow") or ("debug" if blocked else "test"),
                "recommended_action": entry.get("recommended_action") or "Inspect the latest run result before moving on.",
                "alternatives": as_string_list(entry.get("warnings"))[:2] or next_steps[:1],
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
        return {
            "status": "active",
            "primary_kind": kind,
            "current_focus": f"Chain: {entry['label']}",
            "current_stage": entry["current_stage"],
            "suggested_workflow": "session",
            "recommended_action": f"Advance chain '{entry['label']}' to the next stage: {next_steps[0]}." if next_steps else f"Continue the active chain: {entry['label']}.",
            "alternatives": next_steps[1:3] or risks[:1],
        }
    return {
        "status": "empty",
        "primary_kind": None,
        "current_focus": "No workflow state recorded.",
        "current_stage": None,
        "suggested_workflow": "map-codebase",
        "recommended_action": "Run `doctor` and `map-codebase` to establish repo health and a durable brownfield summary before editing.",
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
