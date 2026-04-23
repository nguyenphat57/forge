from __future__ import annotations

from workflow_state_io import string_list
from workflow_state_summary import workflow_hint_for_stage


SCHEMA_VERSION = 1


def _canonical_follow_on(required_stage_chain: list[str], current_stage: str | None) -> list[str]:
    if isinstance(current_stage, str) and current_stage in required_stage_chain:
        return required_stage_chain[required_stage_chain.index(current_stage) + 1 :]
    return required_stage_chain


def canonical_stage_summary(
    last_transition: dict | None,
    *,
    current_stage: str | None,
    required_stage_chain: list[str],
    stages: dict,
) -> dict | None:
    active_stage = current_stage.strip() if isinstance(current_stage, str) and current_stage.strip() else None
    transition = last_transition if isinstance(last_transition, dict) else {}
    transition_stage = transition.get("stage_name")
    if not isinstance(transition_stage, str) or not transition_stage.strip():
        transition_stage = active_stage
    if not isinstance(transition_stage, str) or not transition_stage:
        return None

    transition_status = transition.get("stage_status")
    if transition_status == "blocked":
        stage_payload = transition
    else:
        stage_payload = stages.get(active_stage or transition_stage) if isinstance(stages, dict) else None
        if not isinstance(stage_payload, dict):
            stage_payload = transition
    stage_status = stage_payload.get("status") or transition.get("stage_status") or "active"
    next_actions = stage_payload.get("next_actions") if isinstance(stage_payload.get("next_actions"), list) else transition.get("next_actions")
    notes = stage_payload.get("notes") if isinstance(stage_payload.get("notes"), list) else transition.get("notes")
    next_actions = [item for item in next_actions if isinstance(item, str) and item.strip()] if isinstance(next_actions, list) else []
    notes = [item for item in notes if isinstance(item, str) and item.strip()] if isinstance(notes, list) else []
    focus_stage = active_stage or transition_stage
    follow_on = _canonical_follow_on(required_stage_chain, focus_stage)
    alternatives: list[str] = []
    if follow_on:
        alternatives.append(f"After '{focus_stage}', continue into '{follow_on[0]}'.")
    if notes:
        alternatives.extend(notes[:1])

    if stage_status == "blocked":
        suggested_stage = transition.get("next_stage_override") or active_stage or transition_stage
        action = next_actions[0] if next_actions else stage_payload.get("summary") or f"Resolve the blocker for '{transition_stage}'."
        return {
            "status": "blocked",
            "primary_kind": "stage-state",
            "current_focus": f"Blocked workflow stage: {transition_stage}",
            "current_stage": transition_stage,
            "suggested_workflow": workflow_hint_for_stage(suggested_stage, default="debug"),
            "recommended_action": action,
            "alternatives": alternatives[:2],
        }

    action = (
        next_actions[0]
        if next_actions
        else f"Resume the recorded workflow stage '{focus_stage}' before opening new scope."
    )
    return {
        "status": "active",
        "primary_kind": "stage-state",
        "current_focus": f"Recorded workflow stage: {focus_stage}",
        "current_stage": focus_stage,
        "suggested_workflow": workflow_hint_for_stage(focus_stage, default="plan"),
        "recommended_action": action,
        "alternatives": alternatives[:2],
    }


def normalized_last_transition(state: dict) -> dict | None:
    transition = state.get("last_transition")
    if isinstance(transition, dict):
        return transition
    current_stage = state.get("current_stage")
    stages = state.get("stages")
    if not isinstance(current_stage, str) or not current_stage.strip() or not isinstance(stages, dict):
        return None
    payload = stages.get(current_stage)
    if not isinstance(payload, dict):
        return None
    return {
        "kind": state.get("last_recorded_kind"),
        "stage_name": current_stage,
        "stage_status": payload.get("status"),
        "recorded_at": payload.get("recorded_at") or payload.get("updated_at"),
        "transition_id": payload.get("transition_id"),
        "source_path": payload.get("source_path"),
        "event_ref": payload.get("event_ref"),
        "next_actions": payload.get("next_actions"),
        "notes": payload.get("notes"),
        "summary": payload.get("summary"),
    }


def normalize_summary_workflow(summary: dict, current_stage: str | None) -> dict:
    normalized_summary = dict(summary)
    primary_kind = normalized_summary.get("primary_kind")
    default_workflow = {
        "execution-progress": "build",
        "quality-gate": "review",
        "review-state": "review",
        "route-preview": "plan",
        "run-report": "test",
        "stage-state": "plan",
        "ui-progress": "session",
        "chain-status": "session",
    }.get(primary_kind, "session")
    normalized_summary["suggested_workflow"] = workflow_hint_for_stage(
        normalized_summary.get("suggested_workflow") or normalized_summary.get("current_stage") or current_stage,
        default=default_workflow,
    )
    return normalized_summary


def canonical_chain(state: dict) -> list[str]:
    return string_list(state.get("required_stage_chain"))
