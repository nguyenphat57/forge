from __future__ import annotations

from pathlib import Path

from session_state_resolution import (
    filtered_pending_tasks,
    git_handoff_clean,
    pending_tasks,
    session_blocker,
    session_status_value,
    session_task,
)
from workflow_state_resolution import (
    effective_workflow_summary,
    workflow_state_follow_on_stages,
    workflow_state_has_actionable_slice,
    workflow_state_stage,
)
from workflow_state_summary import summary_items, summary_text, workflow_hint_for_stage


def determine_stage(
    *,
    session: dict | None,
    git_state: dict,
    latest_plan: Path | None,
    latest_spec: Path | None,
    workflow_state: dict | None = None,
    codebase_summary: Path | None = None,
    active_change: dict | None = None,
) -> str:
    del codebase_summary, active_change
    summary = effective_workflow_summary(workflow_state, git_state)
    status = summary_text(summary, "status")
    if status == "blocked":
        return "blocked"
    if status == "review-ready":
        return "review-ready"
    if status == "active":
        if summary_text(summary, "primary_kind") == "route-preview":
            return "change-active"
        return "session-active"
    working_on = session.get("working_on") if isinstance(session, dict) else None
    if isinstance(working_on, dict) and isinstance(working_on.get("status"), str) and working_on["status"].strip().lower() == "blocked":
        return "blocked"
    if session_blocker(session):
        return "blocked"
    pending = filtered_pending_tasks(session, git_state)
    session_status = session_status_value(session)
    if pending:
        return "session-active"
    if session_task(session):
        if (
            session_status in {"active", "completed", "idle"}
            and git_handoff_clean(git_state)
            and not workflow_state_has_actionable_slice(workflow_state, git_state)
        ):
            pass
        else:
            return "session-active"
    if workflow_state_has_actionable_slice(workflow_state, git_state):
        return "change-active"
    if git_state["changed_files"] or git_state["untracked_files"]:
        return "active-changes"
    if latest_plan or latest_spec:
        return "planned"
    return "unscoped"


def _extract_markdown_title(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if ":" in title and title.split(":", 1)[0].lower() in {"plan", "spec"}:
                return title.split(":", 1)[1].strip()
            return title
    return path.stem


def build_focus(
    stage: str,
    *,
    session: dict | None,
    latest_plan: Path | None,
    latest_spec: Path | None,
    git_state: dict,
    workflow_state: dict | None = None,
    codebase_summary: Path | None = None,
    active_change: Path | None = None,
    release_readiness: dict | None = None,
    latest_adoption_check: dict | None = None,
) -> str:
    del codebase_summary, active_change, release_readiness, latest_adoption_check
    summary = effective_workflow_summary(workflow_state, git_state)
    workflow_status = summary_text(summary, "status")
    workflow_focus = summary_text(summary, "current_focus")
    workflow_stage = workflow_state_stage(workflow_state)
    pending = filtered_pending_tasks(session, git_state)
    if stage == "blocked":
        return workflow_focus or f"Blocked: {session_blocker(session)}"
    if stage == "review-ready":
        return workflow_focus or "Work slice is ready for review."
    if stage == "session-active":
        if workflow_status == "active" and workflow_focus:
            return workflow_focus
        return f"Session task: {session_task(session) or pending[0]}"
    if stage == "change-active":
        if workflow_focus:
            return workflow_focus
        if workflow_stage:
            return f"Recorded workflow stage: {workflow_stage}"
        return "Recorded workflow slice is still active."
    if stage == "active-changes":
        total = len(git_state["changed_files"]) + len(git_state["untracked_files"])
        return f"Working tree contains {total} changed file(s)."
    if stage == "planned":
        return (
            f"Plan: {_extract_markdown_title(latest_plan)}"
            if latest_plan is not None
            else f"Spec: {_extract_markdown_title(latest_spec)}"
        )
    return "No active work slice detected from repo state."


def build_recommendations(
    *,
    mode: str,
    stage: str,
    session: dict | None,
    git_state: dict,
    latest_plan: Path | None,
    latest_spec: Path | None,
    handover_excerpt: str | None,
    workflow_state: dict | None = None,
    codebase_summary: Path | None = None,
    active_change: dict | None = None,
    release_readiness: dict | None = None,
    latest_adoption_check: dict | None = None,
) -> tuple[str, str, list[str]]:
    del codebase_summary, active_change, release_readiness, latest_adoption_check
    summary = effective_workflow_summary(workflow_state, git_state)
    workflow_action = summary_text(summary, "recommended_action")
    workflow_alternatives = summary_items(summary, "alternatives")
    workflow_stage = workflow_state_stage(workflow_state)
    workflow_name = workflow_hint_for_stage(
        summary_text(summary, "suggested_workflow") or summary_text(summary, "current_stage") or workflow_stage,
        default=workflow_hint_for_stage(
            workflow_stage,
            default={
                "active-changes": "review",
                "blocked": "debug",
                "planned": "plan",
                "review-ready": "review",
                "session-active": "session",
                "change-active": "session",
                "unscoped": "plan",
            }.get(stage, "session"),
        ),
    )
    workflow_follow_on = workflow_state_follow_on_stages(workflow_state)
    if summary and stage in {"blocked", "review-ready", "session-active"} and workflow_name and workflow_action:
        return workflow_name, workflow_action, workflow_alternatives[:1] if mode == "next" else workflow_alternatives[:2]
    plan_path = latest_plan or latest_spec
    plan_kind = "plan" if latest_plan is not None else "spec"
    plan_title = _extract_markdown_title(plan_path)
    pending = filtered_pending_tasks(session, git_state)
    if stage == "blocked":
        blocker = session_blocker(session) or handover_excerpt or "Validate the current blocker."
        alternatives = [f"Re-open the latest {plan_kind} '{plan_title}' to confirm the intended recovery path."] if plan_title else []
        alternatives.append("If the blocker keeps drifting, capture a fresh handover with the missing evidence.")
        return "debug", f"Resolve the blocker first: {blocker}.", alternatives[:2]
    if stage == "session-active":
        primary = f"Resume the highest-priority pending task: {pending[0]}." if pending else f"Continue the active task: {session_task(session)}."
        alternatives: list[str] = []
        if len(pending) > 1:
            alternatives.append(f"Continue secondary pending task: {pending[1]}.")
        if plan_title:
            alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' if priorities changed.")
        return "session", primary, alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "change-active":
        if workflow_name and workflow_action:
            return workflow_name, workflow_action, workflow_alternatives[:1] if mode == "next" else workflow_alternatives[:2]
        if workflow_stage:
            alternatives: list[str] = []
            if workflow_follow_on:
                alternatives.append(f"After '{workflow_stage}', continue into '{workflow_follow_on[0]}'.")
            if plan_title:
                alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' if the recorded stage no longer matches the intended slice.")
            return workflow_hint_for_stage(workflow_stage, default="session"), f"Resume the recorded workflow stage '{workflow_stage}' before opening new scope.", alternatives[:1] if mode == "next" else alternatives[:2]
        return "session", "Resume the recorded workflow slice before opening new scope.", ["Refresh workflow-state if the recorded slice no longer matches reality."][: 1 if mode == "next" else 2]
    if stage == "review-ready":
        alternatives = [f"Re-open the latest {plan_kind} '{plan_title}' if the review uncovered scope drift."] if plan_title else []
        alternatives.append("If review passes cleanly, advance to the next recorded stage instead of opening new scope.")
        return "review", "Run review and the nearest verification pass before resuming implementation.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "active-changes":
        alternatives = [f"Update the latest {plan_kind} '{plan_title}' if the current diff drifted from the intended slice."] if plan_title else []
        alternatives.append("If the slice is already complete, run a review pass and decide whether to merge or continue.")
        return "review", "Review the current changed files and run the nearest verification before adding new edits.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "planned":
        label = plan_title or "the latest plan"
        alternatives = ["If scope is still fuzzy, tighten the plan before writing code.", "If repo health is unclear, run a fast repo verification before implementation."]
        return "plan", f"Start the first concrete slice from {plan_kind} '{label}'.", alternatives[:1] if mode == "next" else alternatives[:2]
    alternatives = [
        "If runtime/browser proof is failing because the runtime looks stale, run runtime doctor on the affected tool before retrying.",
        "Then state one bounded slice so Forge can route directly without reopening broad discovery.",
    ]
    return (
        "plan",
        "Run `python scripts/verify_repo.py --profile fast` if repo health is unclear, then state one bounded slice so Forge can route directly.",
        alternatives[:1] if mode == "next" else alternatives[:2],
    )


def build_evidence(
    *,
    readme: Path | None,
    latest_plan: Path | None,
    latest_spec: Path | None,
    session_path: Path | None,
    handover_path: Path | None,
    git_state: dict,
    preferences_source: dict,
    workflow_source: dict,
    codebase_summary: Path | None = None,
) -> list[str]:
    del codebase_summary
    evidence: list[str] = []
    if readme is not None:
        evidence.append(f"readme: {readme}")
    if latest_plan is not None:
        evidence.append(f"plan: {latest_plan}")
    if latest_spec is not None:
        evidence.append(f"spec: {latest_spec}")
    if session_path is not None and session_path.exists():
        evidence.append(f"session: {session_path}")
    if handover_path is not None and handover_path.exists():
        evidence.append(f"handover: {handover_path}")
    if git_state["changed_files"] or git_state["untracked_files"]:
        evidence.append(f"git: {len(git_state['changed_files']) + len(git_state['untracked_files'])} working tree item(s)")
    if preferences_source["path"]:
        evidence.append(f"preferences: {preferences_source['path']}")
    if workflow_source.get("path"):
        evidence.append(f"workflow-state: {workflow_source['path']}")
    return evidence
