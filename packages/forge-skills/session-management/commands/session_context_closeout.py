from __future__ import annotations

import argparse
from pathlib import Path

from session_context_continuity import (
    append_closeout_entries,
    handover_requested,
    has_closeout_signals,
    has_session_signals,
)
from session_context_io import build_handover_text, dedupe, now_iso, write_session
from session_context_workspace import read_git_status


OWNER = "forge-session-management"


def build_closeout_report(workspace: Path, args: argparse.Namespace) -> dict:
    brain_dir = workspace / ".brain"
    if not has_closeout_signals(args):
        return _report(workspace, "skipped", None, None, [])

    git_state = read_git_status(workspace)
    session_path = brain_dir / "session.json"
    handover_path = brain_dir / "handover.md"
    session_file: str | None = None
    handover_file: str | None = None
    continuity_files = append_closeout_entries(brain_dir, args, scope=workspace.name)
    if has_session_signals(args):
        changed_files = [*git_state.get("changed_files", []), *git_state.get("untracked_files", [])]
        payload = {
            "updated_at": now_iso(),
            "working_on": {
                "feature": workspace.name,
                "task": args.task or workspace.name,
                "status": args.status or ("blocked" if args.blocker else "completed"),
                "files": dedupe(args.file + changed_files[:12]),
            },
            "pending_tasks": dedupe(args.pending),
            "recent_changes": changed_files[:20],
            "verification": dedupe(args.verification),
            "decisions_made": dedupe(args.decision),
            "risks": dedupe(args.risk),
            "blockers": dedupe(args.blocker),
            "source_artifacts": continuity_files,
        }
        write_session(session_path, payload)
        session_file = str(session_path)
        if handover_requested(args):
            next_step = payload["pending_tasks"][0] if payload["pending_tasks"] else None
            handover_path.write_text(build_handover_text(payload, next_step=next_step), encoding="utf-8")
            handover_file = str(handover_path)
    return _report(workspace, "saved", session_file, handover_file, continuity_files)


def _report(workspace: Path, action: str, session_file: str | None, handover_file: str | None, continuity_files: list[str]) -> dict:
    return {
        "status": "PASS",
        "owner": OWNER,
        "mode": "closeout",
        "workspace": str(workspace),
        "continuity_action": action,
        "session_file": session_file,
        "handover_file": handover_file,
        "continuity_files": continuity_files,
        "warnings": [],
    }
