from __future__ import annotations

from _forge_core_command import bootstrap_shared_paths

bootstrap_shared_paths()

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio
from help_next_support import (
    filter_stale_session_items,
    git_worktree_clean,
    read_git_status,
    read_handover_excerpt,
    read_json_object,
    session_blocker,
    session_status_value,
    workflow_state_has_actionable_slice,
)
from resolve_help_next import build_report as build_help_next_report
from workflow_state_support import resolve_workflow_state


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in items:
        candidate = item.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        merged.append(candidate)
    return merged


def _session_task(session: dict | None) -> str | None:
    if not isinstance(session, dict):
        return None
    working_on = session.get("working_on")
    if not isinstance(working_on, dict):
        return None
    for key in ("task", "feature"):
        value = working_on.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _session_files(session: dict | None) -> list[str]:
    if not isinstance(session, dict):
        return []
    working_on = session.get("working_on")
    if not isinstance(working_on, dict):
        return []
    return _string_list(working_on.get("files"))


def _session_blockers(session: dict | None) -> list[str]:
    if not isinstance(session, dict):
        return []
    for key in ("blockers", "blocker"):
        value = session.get(key)
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        if isinstance(value, list):
            return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _workspace_path_strings(workspace: Path, files: list[str]) -> list[str]:
    resolved: list[str] = []
    for file_name in files:
        candidate = Path(file_name)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        resolved.append(str(candidate))
    return resolved


def _load_session(path: Path, warnings: list[str]) -> dict | None:
    if not path.exists():
        return None
    return read_json_object(path, "session context", warnings)


def _build_handover_text(payload: dict, *, next_step: str | None) -> str:
    task = payload["working_on"]["task"] or payload["working_on"]["feature"] or "(none)"
    lines = [
        "HANDOVER",
        f"- Current task: {task}",
        f"- Status: {payload['working_on']['status'] or '(none)'}",
    ]
    if payload["pending_tasks"]:
        lines.append("- Pending:")
        for item in payload["pending_tasks"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Pending: (none)")
    if payload["verification"]:
        lines.append("- Verification run:")
        for item in payload["verification"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Verification run: (none)")
    if payload["decisions_made"]:
        lines.append("- Important decisions:")
        for item in payload["decisions_made"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Important decisions: (none)")
    if payload["risks"]:
        lines.append("- Risks:")
        for item in payload["risks"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Risks: (none)")
    blockers = _string_list(payload.get("blockers"))
    if blockers:
        lines.append("- Blockers:")
        for item in blockers:
            lines.append(f"  - {item}")
    else:
        lines.append("- Blockers: (none)")
    lines.append(f"- Next step: {next_step or '(none)'}")
    return "\n".join(lines) + "\n"


def build_save_report(workspace: Path, args: argparse.Namespace) -> dict:
    warnings: list[str] = []
    navigator = build_help_next_report(workspace, "next")
    workflow_report = resolve_workflow_state(workspace, warnings)
    workflow_state = workflow_report["state"] if isinstance(workflow_report, dict) else None
    git_state = read_git_status(workspace)

    session_path = workspace / ".brain" / "session.json"
    existing_session = _load_session(session_path, warnings)
    handover_path = workspace / ".brain" / "handover.md"

    session_path.parent.mkdir(parents=True, exist_ok=True)

    current_focus = navigator.get("current_focus")
    feature = args.feature or ""
    if not feature and isinstance(existing_session, dict):
        working_on = existing_session.get("working_on")
        if isinstance(working_on, dict):
            feature = str(working_on.get("feature") or "").strip()
    if not feature and isinstance(workflow_state, dict):
        feature = str(workflow_state.get("project") or "").strip()
    if not feature:
        feature = workspace.name

    task = args.task or _session_task(existing_session) or (current_focus if isinstance(current_focus, str) else "") or feature
    changed_files = [*git_state.get("changed_files", []), *git_state.get("untracked_files", [])]
    files = _dedupe(args.file + _session_files(existing_session) + changed_files[:12])
    navigator_stage = str(navigator.get("current_stage") or "").strip().casefold()
    existing_pending, _ = filter_stale_session_items(
        _string_list((existing_session or {}).get("pending_tasks")),
        git_state,
        risk_mode=False,
    )
    pending_tasks = _dedupe(
        args.pending
        + ([args.next_step] if args.next_step else [])
        + existing_pending
    )
    if (
        not pending_tasks
        and navigator_stage
        and navigator_stage != "unscoped"
        and isinstance(navigator.get("recommended_action"), str)
        and navigator["recommended_action"].strip()
    ):
        suggested_pending, _ = filter_stale_session_items(
            [navigator["recommended_action"].strip()],
            git_state,
            risk_mode=False,
        )
        pending_tasks = suggested_pending
    verification = _dedupe(args.verification + _string_list((existing_session or {}).get("verification")))
    decisions_made = _dedupe(args.decision + _string_list((existing_session or {}).get("decisions_made")))
    risks = _dedupe(args.risk + _string_list((existing_session or {}).get("risks")))
    blockers = _dedupe(args.blocker + _session_blockers(existing_session))
    best_next_candidates = [args.next_step] if args.next_step else []
    if (
        navigator_stage
        and navigator_stage != "unscoped"
        and isinstance(navigator.get("recommended_action"), str)
        and navigator["recommended_action"].strip()
    ):
        best_next_candidates.append(navigator["recommended_action"].strip())
    filtered_best_next, _ = filter_stale_session_items(best_next_candidates, git_state, risk_mode=False)
    best_next_step = filtered_best_next[0] if filtered_best_next else None

    status = args.status or session_status_value(existing_session)
    actionable_workflow_state = workflow_state_has_actionable_slice(workflow_state, git_state)
    if status == "active" and not pending_tasks and not changed_files and not actionable_workflow_state:
        status = "completed"
    if not status:
        status = "active" if pending_tasks or changed_files or actionable_workflow_state else "idle"
    if status in {"completed", "idle"} and not pending_tasks and not changed_files and not actionable_workflow_state:
        best_next_step = None

    payload = {
        "updated_at": _now_iso(),
        "working_on": {
            "feature": feature,
            "task": task,
            "status": status,
            "files": files,
        },
        "pending_tasks": pending_tasks,
        "recent_changes": changed_files[:20],
        "verification": verification,
        "decisions_made": decisions_made,
        "risks": risks,
        "blockers": blockers,
        "source_artifacts": _dedupe(navigator.get("evidence", [])),
    }
    session_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    wrote_handover = False
    if args.write_handover:
        handover_path.write_text(
            _build_handover_text(payload, next_step=best_next_step),
            encoding="utf-8",
        )
        wrote_handover = True

    return {
        "status": "PASS",
        "mode": "save",
        "workspace": str(workspace),
        "session_file": str(session_path),
        "handover_file": str(handover_path) if wrote_handover else None,
        "current_stage": navigator.get("current_stage"),
        "current_focus": current_focus,
        "best_next_step": best_next_step,
        "session": payload,
        "warnings": _dedupe(warnings + navigator.get("warnings", [])),
    }


def build_resume_report(workspace: Path) -> dict:
    warnings: list[str] = []
    navigator = build_help_next_report(workspace, "next")
    workflow_report = resolve_workflow_state(workspace, warnings)
    git_state = read_git_status(workspace)
    session_path = workspace / ".brain" / "session.json"
    session = _load_session(session_path, warnings)
    handover_path = workspace / ".brain" / "handover.md"
    handover_excerpt = read_handover_excerpt(handover_path)

    signals = navigator.get("signals", {})
    important_artifacts = _dedupe(
        [
            item
            for item in (
                signals.get("workflow_state_file"),
                signals.get("latest_plan"),
                signals.get("latest_spec"),
                signals.get("active_change_status"),
                signals.get("session_file"),
                signals.get("handover_file"),
            )
            if isinstance(item, str) and item.strip()
        ]
        + _workspace_path_strings(workspace, _session_files(session))
    )
    session_pending = _string_list((session or {}).get("pending_tasks"))
    pending_work, filtered_pending = filter_stale_session_items(session_pending, git_state, risk_mode=False)
    if not pending_work and isinstance(navigator.get("recommended_action"), str) and navigator["recommended_action"].strip():
        pending_work = [navigator["recommended_action"].strip()]

    session_risks = _string_list((session or {}).get("risks"))
    filtered_risks, filtered_risk_count = filter_stale_session_items(session_risks, git_state, risk_mode=True)
    risks_or_assumptions = _dedupe(
        filtered_risks
        + ([session_blocker(session)] if session_blocker(session) else [])
        + ([handover_excerpt] if handover_excerpt else [])
    )
    relevant_continuity = _dedupe(
        ([handover_excerpt] if handover_excerpt else [])
        + _string_list((session or {}).get("decisions_made"))[:3]
        + [f"Verification: {item}" for item in _string_list((session or {}).get("verification"))[:2]]
    )

    status = "PASS"
    combined_warnings = _dedupe(warnings + navigator.get("warnings", []))
    filtered_items = filtered_pending + filtered_risk_count
    if filtered_items:
        combined_warnings.append(
            f"Filtered {filtered_items} stale session item(s) that no longer match the current git state."
        )
    if (
        navigator.get("current_stage") == "unscoped"
        and not session
        and workflow_report.get("state") is None
        and not handover_excerpt
    ):
        status = "WARN"

    return {
        "status": status,
        "mode": "resume",
        "workspace": str(workspace),
        "current_stage": navigator.get("current_stage"),
        "current_focus": navigator.get("current_focus"),
        "important_files_or_artifacts": important_artifacts,
        "pending_work": pending_work,
        "risks_or_assumptions": risks_or_assumptions,
        "best_next_step": navigator.get("recommended_action"),
        "relevant_continuity": relevant_continuity,
        "restored_from": _dedupe(navigator.get("evidence", [])),
        "session_file": str(session_path) if session_path.exists() else None,
        "handover_file": str(handover_path) if handover_path.exists() else None,
        "warnings": combined_warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Session Context",
        f"- Status: {report['status']}",
        f"- Mode: {report['mode']}",
        f"- Workspace: {report['workspace']}",
    ]
    if report["mode"] == "save":
        lines.extend(
            [
                f"- Session file: {report['session_file']}",
                f"- Handover file: {report['handover_file'] or '(not written)'}",
                f"- Current stage: {report['current_stage'] or '(none)'}",
                f"- Current focus: {report['current_focus'] or '(none)'}",
                f"- Best next step: {report['best_next_step'] or '(none)'}",
            ]
        )
    else:
        lines.extend(
            [
                f"- Current stage: {report['current_stage'] or '(none)'}",
                f"- Current focus: {report['current_focus'] or '(none)'}",
                f"- Best next step: {report['best_next_step'] or '(none)'}",
            ]
        )
        for label, values in (
            ("Important files or artifacts", report["important_files_or_artifacts"]),
            ("Pending work", report["pending_work"]),
            ("Risks or assumptions", report["risks_or_assumptions"]),
            ("Relevant continuity", report["relevant_continuity"]),
            ("Restored from", report["restored_from"]),
        ):
            if values:
                lines.append(f"- {label}:")
                for value in values:
                    lines.append(f"  - {value}")
            else:
                lines.append(f"- {label}: (none)")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Persist or restore Forge session context from durable artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    save_parser = subparsers.add_parser("save", help="Persist the current task context into .brain/session.json")
    save_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    save_parser.add_argument("--feature", default="", help="Optional feature or workstream label")
    save_parser.add_argument("--task", default="", help="Optional task label")
    save_parser.add_argument("--status", default="", help="Optional task status")
    save_parser.add_argument("--file", action="append", default=[], help="Relevant file path. Repeatable.")
    save_parser.add_argument("--pending", action="append", default=[], help="Pending task. Repeatable.")
    save_parser.add_argument("--verification", action="append", default=[], help="Verification already run. Repeatable.")
    save_parser.add_argument("--decision", action="append", default=[], help="Important decision to persist. Repeatable.")
    save_parser.add_argument("--risk", action="append", default=[], help="Residual risk or blocker. Repeatable.")
    save_parser.add_argument("--blocker", action="append", default=[], help="Active blocker to preserve. Repeatable.")
    save_parser.add_argument("--next-step", default="", help="Optional best next step to pin into pending tasks")
    save_parser.add_argument("--write-handover", action="store_true", help="Also refresh .brain/handover.md")
    save_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    resume_parser = subparsers.add_parser("resume", help="Restore context from repo state and persisted session artifacts")
    resume_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    resume_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()
    workspace = args.workspace.resolve()

    if args.command == "save":
        report = build_save_report(workspace, args)
    else:
        report = build_resume_report(workspace)

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
