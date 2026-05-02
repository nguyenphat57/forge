from __future__ import annotations

import argparse
from pathlib import Path

from operator_state_resolution import (
    filter_stale_session_items,
    session_blocker,
    session_status_value,
    workflow_state_has_actionable_slice,
)
from workflow_state_support import resolve_workflow_state

from session_context_continuity import relevant_brain_continuity
from session_context_io import (
    build_handover_text,
    dedupe,
    load_session,
    now_iso,
    session_blockers,
    session_files,
    session_task,
    string_list,
    workspace_path_strings,
    write_session,
)
from session_context_navigator import build_session_navigator
from session_context_workspace import (
    read_git_status,
    read_handover_excerpt,
)


OWNER = "forge-session-management"


def build_save_report(workspace: Path, args: argparse.Namespace) -> dict:
    warnings: list[str] = []
    navigator = build_session_navigator(workspace, "next", warnings)
    workflow_report = resolve_workflow_state(workspace, warnings)
    workflow_state = workflow_report["state"] if isinstance(workflow_report, dict) else None
    git_state = read_git_status(workspace)
    session_path = workspace / ".brain" / "session.json"
    existing_session = load_session(session_path, warnings)
    handover_path = workspace / ".brain" / "handover.md"

    current_focus = navigator.get("current_focus")
    feature = args.feature or _existing_feature(existing_session) or _workflow_project(workflow_state) or workspace.name
    task = args.task or session_task(existing_session) or (current_focus if isinstance(current_focus, str) else "") or feature
    changed_files = [*git_state.get("changed_files", []), *git_state.get("untracked_files", [])]
    files = dedupe(args.file + session_files(existing_session) + changed_files[:12])
    navigator_stage = str(navigator.get("current_stage") or "").strip().casefold()
    existing_pending, _ = filter_stale_session_items(
        string_list((existing_session or {}).get("pending_tasks")),
        git_state,
        risk_mode=False,
    )
    pending_tasks = _pending_tasks(args, existing_pending, navigator, navigator_stage, git_state)
    verification = dedupe(args.verification + string_list((existing_session or {}).get("verification")))
    decisions_made = dedupe(args.decision + string_list((existing_session or {}).get("decisions_made")))
    risks = dedupe(args.risk + string_list((existing_session or {}).get("risks")))
    blockers = dedupe(args.blocker + session_blockers(existing_session))
    best_next_step = _best_next_step(args, navigator, navigator_stage, git_state)
    status = _resolved_status(args.status, existing_session, pending_tasks, changed_files, workflow_state, git_state)
    if status in {"completed", "idle"} and not pending_tasks and not changed_files:
        if not workflow_state_has_actionable_slice(workflow_state, git_state):
            best_next_step = None

    payload = {
        "updated_at": now_iso(),
        "working_on": {"feature": feature, "task": task, "status": status, "files": files},
        "pending_tasks": pending_tasks,
        "recent_changes": changed_files[:20],
        "verification": verification,
        "decisions_made": decisions_made,
        "risks": risks,
        "blockers": blockers,
        "source_artifacts": dedupe(navigator.get("evidence", [])),
    }
    write_session(session_path, payload)
    wrote_handover = _write_handover_if_requested(args, handover_path, payload, best_next_step)
    return {
        "status": "PASS",
        "owner": OWNER,
        "mode": "save",
        "workspace": str(workspace),
        "session_file": str(session_path),
        "handover_file": str(handover_path) if wrote_handover else None,
        "current_stage": navigator.get("current_stage"),
        "current_focus": current_focus,
        "best_next_step": best_next_step,
        "session": payload,
        "warnings": dedupe(warnings + navigator.get("warnings", [])),
    }


def build_resume_report(workspace: Path) -> dict:
    warnings: list[str] = []
    navigator = build_session_navigator(workspace, "next", warnings)
    workflow_report = resolve_workflow_state(workspace, warnings)
    git_state = read_git_status(workspace)
    session_path = workspace / ".brain" / "session.json"
    session = load_session(session_path, warnings)
    handover_path = workspace / ".brain" / "handover.md"
    handover_excerpt = read_handover_excerpt(handover_path)
    brain_continuity = relevant_brain_continuity(workspace / ".brain", warnings)
    signals = navigator.get("signals", {})
    pending_work, filtered_pending = filter_stale_session_items(
        string_list((session or {}).get("pending_tasks")),
        git_state,
        risk_mode=False,
    )
    if not pending_work and isinstance(navigator.get("recommended_action"), str):
        if navigator["recommended_action"].strip():
            pending_work = [navigator["recommended_action"].strip()]
    risks_or_assumptions, filtered_risk_count = _resume_risks(session, handover_excerpt, git_state)
    status = _resume_status(navigator, workflow_report, session, handover_excerpt, brain_continuity)
    combined_warnings = dedupe(warnings + navigator.get("warnings", []))
    filtered_items = filtered_pending + filtered_risk_count
    if filtered_items:
        combined_warnings.append(f"Filtered {filtered_items} stale session item(s) that no longer match the current git state.")
    return {
        "status": status,
        "owner": OWNER,
        "mode": "resume",
        "workspace": str(workspace),
        "current_stage": navigator.get("current_stage"),
        "current_focus": navigator.get("current_focus"),
        "important_files_or_artifacts": _important_artifacts(workspace, signals, session),
        "pending_work": pending_work,
        "risks_or_assumptions": risks_or_assumptions,
        "best_next_step": navigator.get("recommended_action"),
        "relevant_continuity": _relevant_continuity(session, handover_excerpt, brain_continuity),
        "restored_from": dedupe(navigator.get("evidence", [])),
        "session_file": str(session_path) if session_path.exists() else None,
        "handover_file": str(handover_path) if handover_path.exists() else None,
        "warnings": combined_warnings,
    }


def format_text(report: dict) -> str:
    lines = ["Forge Session Context", f"- Status: {report['status']}", f"- Owner: {report['owner']}", f"- Mode: {report['mode']}", f"- Workspace: {report['workspace']}"]
    if report["mode"] == "save":
        lines.extend([
            f"- Session file: {report['session_file']}",
            f"- Handover file: {report['handover_file'] or '(not written)'}",
            f"- Current stage: {report['current_stage'] or '(none)'}",
            f"- Current focus: {report['current_focus'] or '(none)'}",
            f"- Best next step: {report['best_next_step'] or '(none)'}",
        ])
    elif report["mode"] == "closeout":
        lines.extend([
            f"- Continuity action: {report['continuity_action']}",
            f"- Session file: {report['session_file'] or '(not written)'}",
            f"- Handover file: {report['handover_file'] or '(not written)'}",
        ])
        for path in report["continuity_files"]:
            lines.append(f"- Continuity file: {path}")
    else:
        lines.extend([
            f"- Current stage: {report['current_stage'] or '(none)'}",
            f"- Current focus: {report['current_focus'] or '(none)'}",
            f"- Best next step: {report['best_next_step'] or '(none)'}",
        ])
        _append_report_sections(lines, report)
    _append_warnings(lines, report["warnings"])
    return "\n".join(lines)


def _existing_feature(session: dict | None) -> str:
    working_on = (session or {}).get("working_on")
    return str((working_on or {}).get("feature") or "").strip() if isinstance(working_on, dict) else ""


def _workflow_project(workflow_state: object) -> str:
    return str((workflow_state or {}).get("project") or "").strip() if isinstance(workflow_state, dict) else ""


def _pending_tasks(args: argparse.Namespace, existing_pending: list[str], navigator: dict, stage: str, git_state: dict) -> list[str]:
    pending_tasks = dedupe(args.pending + ([args.next_step] if args.next_step else []) + existing_pending)
    if not pending_tasks and stage and stage != "unscoped" and isinstance(navigator.get("recommended_action"), str):
        suggested, _ = filter_stale_session_items([navigator["recommended_action"].strip()], git_state, risk_mode=False)
        pending_tasks = suggested
    return pending_tasks


def _best_next_step(args: argparse.Namespace, navigator: dict, stage: str, git_state: dict) -> str | None:
    candidates = [args.next_step] if args.next_step else []
    if stage and stage != "unscoped" and isinstance(navigator.get("recommended_action"), str):
        candidates.append(navigator["recommended_action"].strip())
    filtered, _ = filter_stale_session_items(candidates, git_state, risk_mode=False)
    return filtered[0] if filtered else None


def _resolved_status(status: str, session: dict | None, pending: list[str], changed: list[str], workflow_state: object, git_state: dict) -> str:
    resolved = status or session_status_value(session)
    actionable = workflow_state_has_actionable_slice(workflow_state, git_state)
    if resolved == "active" and not pending and not changed and not actionable:
        return "completed"
    return resolved or ("active" if pending or changed or actionable else "idle")


def _write_handover_if_requested(args: argparse.Namespace, path: Path, payload: dict, next_step: str | None) -> bool:
    if not args.write_handover:
        return False
    path.write_text(build_handover_text(payload, next_step=next_step), encoding="utf-8")
    return True


def _important_artifacts(workspace: Path, signals: dict, session: dict | None) -> list[str]:
    values = [signals.get(key) for key in ("workflow_state_file", "latest_plan", "latest_spec", "active_change_status", "session_file", "handover_file")]
    return dedupe([item for item in values if isinstance(item, str) and item.strip()] + workspace_path_strings(workspace, session_files(session)))


def _resume_risks(session: dict | None, handover_excerpt: str | None, git_state: dict) -> tuple[list[str], int]:
    filtered_risks, count = filter_stale_session_items(string_list((session or {}).get("risks")), git_state, risk_mode=True)
    risks = dedupe(filtered_risks + ([session_blocker(session)] if session_blocker(session) else []) + ([handover_excerpt] if handover_excerpt else []))
    return risks, count


def _relevant_continuity(session: dict | None, handover_excerpt: str | None, brain_continuity: list[str]) -> list[str]:
    return dedupe(([handover_excerpt] if handover_excerpt else []) + string_list((session or {}).get("decisions_made"))[:3] + [f"Verification: {item}" for item in string_list((session or {}).get("verification"))[:2]] + brain_continuity)


def _resume_status(navigator: dict, workflow_report: dict, session: dict | None, handover: str | None, brain_continuity: list[str]) -> str:
    if navigator.get("current_stage") == "unscoped" and not session and workflow_report.get("state") is None and not handover and not brain_continuity:
        return "WARN"
    return "PASS"


def _append_report_sections(lines: list[str], report: dict) -> None:
    for label, values in (
        ("Important files or artifacts", report["important_files_or_artifacts"]),
        ("Pending work", report["pending_work"]),
        ("Risks or assumptions", report["risks_or_assumptions"]),
        ("Relevant continuity", report["relevant_continuity"]),
        ("Restored from", report["restored_from"]),
    ):
        lines.append(f"- {label}:" if values else f"- {label}: (none)")
        for value in values:
            lines.append(f"  - {value}")


def _append_warnings(lines: list[str], warnings: list[str]) -> None:
    lines.append("- Warnings:" if warnings else "- Warnings: (none)")
    for item in warnings:
        lines.append(f"  - {item}")
