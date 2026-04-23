from __future__ import annotations

from session_state_resolution import git_handoff_clean
from workflow_state_summary import summary_text, workflow_summary


def workflow_state_stage(workflow_state: dict | None) -> str | None:
    if not isinstance(workflow_state, dict):
        return None
    current_stage = workflow_state.get("current_stage")
    return current_stage.strip() if isinstance(current_stage, str) and current_stage.strip() else None


def workflow_state_required_chain(workflow_state: dict | None) -> list[str]:
    if not isinstance(workflow_state, dict):
        return []
    required_stage_chain = workflow_state.get("required_stage_chain")
    if not isinstance(required_stage_chain, list):
        return []
    return [item.strip() for item in required_stage_chain if isinstance(item, str) and item.strip()]


def workflow_state_has_recorded_slice(workflow_state: dict | None) -> bool:
    if not isinstance(workflow_state, dict):
        return False
    if workflow_state_stage(workflow_state):
        return True
    if workflow_state_required_chain(workflow_state):
        return True
    stages = workflow_state.get("stages")
    return isinstance(stages, dict) and bool(stages)


def workflow_summary_is_stale_merge_handoff(summary: dict | None, git_state: dict) -> bool:
    if not git_handoff_clean(git_state):
        return False
    if summary_text(summary, "status") != "active":
        return False
    current_focus = summary_text(summary, "current_focus") or ""
    recommended_action = summary_text(summary, "recommended_action") or ""
    suggested_workflow = summary_text(summary, "suggested_workflow") or ""
    primary_kind = summary_text(summary, "primary_kind") or ""
    focus_lower = current_focus.casefold()
    action_lower = recommended_action.casefold()
    if "ready-for-merge" not in focus_lower and "ready-for-merge" not in action_lower:
        return False
    if primary_kind == "quality-gate":
        return "gate approved" in focus_lower or "approved handoff" in action_lower
    return suggested_workflow == "review" and "approved handoff" in action_lower


def effective_workflow_summary(workflow_state: dict | None, git_state: dict) -> dict | None:
    summary = workflow_summary(workflow_state)
    return None if workflow_summary_is_stale_merge_handoff(summary, git_state) else summary


def workflow_state_has_actionable_slice(workflow_state: dict | None, git_state: dict) -> bool:
    if workflow_summary_is_stale_merge_handoff(workflow_summary(workflow_state), git_state):
        return False
    return workflow_state_has_recorded_slice(workflow_state)


def workflow_state_follow_on_stages(workflow_state: dict | None) -> list[str]:
    current_stage = workflow_state_stage(workflow_state)
    required_stage_chain = workflow_state_required_chain(workflow_state)
    if current_stage and current_stage in required_stage_chain:
        return required_stage_chain[required_stage_chain.index(current_stage) + 1 :]
    return required_stage_chain
