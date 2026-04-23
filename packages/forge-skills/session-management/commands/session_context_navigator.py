from __future__ import annotations

from pathlib import Path

from operator_state_resolution import (
    build_evidence,
    build_focus,
    build_recommendations,
    determine_stage,
    effective_workflow_summary,
    workflow_summary_is_stale_merge_handoff,
)
from workflow_state_support import resolve_workflow_state

from session_context_io import load_session
from session_context_workspace import (
    collect_repo_signals,
    extract_markdown_title,
    find_latest_markdown,
    first_existing_file,
    read_git_status,
    read_handover_excerpt,
)


def build_session_navigator(workspace: Path, mode: str, warnings: list[str]) -> dict:
    readme = first_existing_file(workspace, ("README.md", "README"))
    latest_plan = find_latest_markdown(workspace, "docs/plans")
    latest_spec = find_latest_markdown(workspace, "docs/specs")
    session_path = workspace / ".brain" / "session.json"
    session = load_session(session_path, warnings)
    handover_path = workspace / ".brain" / "handover.md"
    handover_excerpt = read_handover_excerpt(handover_path)
    git_state = read_git_status(workspace)
    workflow_report = resolve_workflow_state(workspace, warnings, auto_seed_missing=True)
    workflow_state = workflow_report["state"]
    has_continuity_sidecars = _append_continuity_warnings(
        warnings,
        workflow_state=workflow_state,
        session_path=session_path,
        handover_path=handover_path,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
    )
    if workflow_summary_is_stale_merge_handoff(
        (workflow_state or {}).get("summary") if isinstance(workflow_state, dict) else None,
        git_state,
    ):
        warnings.append("Filtered stale merge-ready workflow-state because the repo is already clean and synced.")

    stage = determine_stage(
        session=session,
        git_state=git_state,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        workflow_state=workflow_state,
    )
    focus = build_focus(
        stage,
        session=session,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        git_state=git_state,
        workflow_state=workflow_state,
    )
    suggested_workflow, recommended_action, alternatives = build_recommendations(
        mode=mode,
        stage=stage,
        session=session,
        git_state=git_state,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        handover_excerpt=handover_excerpt,
        workflow_state=workflow_state,
        has_continuity_sidecars=has_continuity_sidecars,
    )
    return {
        "current_stage": stage,
        "current_focus": focus,
        "suggested_workflow": suggested_workflow,
        "recommended_action": recommended_action,
        "alternatives": alternatives,
        "signals": _signals(workspace, git_state, latest_plan, latest_spec, session_path, handover_path, readme, workflow_report, workflow_state),
        "evidence": build_evidence(
            readme=readme,
            latest_plan=latest_plan,
            latest_spec=latest_spec,
            session_path=session_path,
            handover_path=handover_path,
            git_state=git_state,
            preferences_source={"path": None},
            workflow_source=workflow_report,
        ),
        "warnings": warnings,
    }


def _append_continuity_warnings(
    warnings: list[str],
    *,
    workflow_state: object,
    session_path: Path,
    handover_path: Path,
    latest_plan: Path | None,
    latest_spec: Path | None,
) -> bool:
    if workflow_state is not None:
        return False
    has_sidecars = False
    if session_path.exists():
        warnings.append("Session context is available only as continuity sidecar.")
        has_sidecars = True
    if handover_path.exists():
        warnings.append("Handover notes are available only as continuity sidecar.")
        has_sidecars = True
    if latest_plan or latest_spec:
        warnings.append("Plan/spec docs are present but canonical workflow-state is unavailable.")
    return has_sidecars


def _signals(
    workspace: Path,
    git_state: dict,
    latest_plan: Path | None,
    latest_spec: Path | None,
    session_path: Path,
    handover_path: Path,
    readme: Path | None,
    workflow_report: dict,
    workflow_state: object,
) -> dict:
    return {
        "repo_signals": collect_repo_signals(workspace),
        "changed_files": git_state["changed_files"],
        "untracked_files": git_state["untracked_files"],
        "latest_plan": str(latest_plan) if latest_plan else None,
        "latest_plan_title": extract_markdown_title(latest_plan),
        "latest_spec": str(latest_spec) if latest_spec else None,
        "latest_spec_title": extract_markdown_title(latest_spec),
        "session_file": str(session_path) if session_path.exists() else None,
        "handover_file": str(handover_path) if handover_path.exists() else None,
        "readme": str(readme) if readme else None,
        "workflow_state_file": workflow_report["path"],
        "workflow_state_source": workflow_report["source"],
        "workflow_summary": effective_workflow_summary(workflow_state, git_state),
        "workflow_packet_index": workflow_state.get("packet_index") if isinstance(workflow_state, dict) else None,
    }
