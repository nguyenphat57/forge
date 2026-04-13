from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, load_preferences, resolve_response_style
from help_next_support import (
    build_evidence,
    build_focus,
    build_recommendations,
    collect_repo_signals,
    determine_stage,
    effective_workflow_summary,
    extract_markdown_title,
    find_latest_markdown,
    find_latest_json,
    find_latest_named_file,
    first_existing_file,
    read_git_status,
    read_handover_excerpt,
    read_json_object,
    workflow_summary_is_stale_merge_handoff,
)
from workflow_state_support import resolve_workflow_state


def build_report(workspace: Path, mode: str) -> dict:
    warnings: list[str] = []
    preferences_report = load_preferences(workspace=workspace)
    response_style = resolve_response_style(preferences_report["preferences"])
    warnings.extend(preferences_report["warnings"])

    readme = first_existing_file(workspace, ("README.md", "README"))
    latest_plan = find_latest_markdown(workspace, "docs/plans")
    latest_spec = find_latest_markdown(workspace, "docs/specs")
    packet_index_sidecar = find_latest_named_file(workspace, ".forge-artifacts/workflow-state", "packet-index.json")
    session_path = workspace / ".brain" / "session.json"
    session = read_json_object(session_path, "session context", warnings)
    handover_path = workspace / ".brain" / "handover.md"
    handover_excerpt = read_handover_excerpt(handover_path)
    git_state = read_git_status(workspace)
    repo_signals = collect_repo_signals(workspace)
    workflow_report = resolve_workflow_state(workspace, warnings)
    workflow_state = workflow_report["state"]
    filtered_workflow_summary = effective_workflow_summary(workflow_state, git_state)
    has_bootstrap_sidecars = False
    if workflow_state is None:
        if session_path.exists():
            warnings.append("Session context is available only as continuity sidecar.")
            has_bootstrap_sidecars = True
        if handover_path.exists():
            warnings.append("Handover notes are available only as continuity sidecar.")
            has_bootstrap_sidecars = True
        if latest_plan or latest_spec:
            warnings.append("Plan/spec docs are sidecars until canonical workflow-state is seeded.")
            has_bootstrap_sidecars = True
        if packet_index_sidecar is not None:
            warnings.append("Packet index is a sidecar until canonical workflow-state is seeded.")
            has_bootstrap_sidecars = True
    if workflow_summary_is_stale_merge_handoff((workflow_state or {}).get("summary") if isinstance(workflow_state, dict) else None, git_state):
        warnings.append("Filtered stale merge-ready workflow-state because the repo is already clean and synced.")

    stage = determine_stage(
        session=session,
        git_state=git_state,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        workflow_state=workflow_state,
    )
    if stage == "unscoped":
        if not session_path.exists():
            warnings.append("No session context found.")
        if not latest_plan and not latest_spec:
            warnings.append("No active plan or spec found.")

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
        has_bootstrap_sidecars=has_bootstrap_sidecars,
    )

    return {
        "status": "WARN" if warnings else "PASS",
        "mode": mode,
        "workspace": str(workspace),
        "current_stage": stage,
        "current_focus": focus,
        "suggested_workflow": suggested_workflow,
        "recommended_action": recommended_action,
        "alternatives": alternatives,
        "signals": {
            "repo_signals": repo_signals,
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
            "workflow_summary": filtered_workflow_summary,
            "workflow_packet_index": workflow_state.get("packet_index") if isinstance(workflow_state, dict) else None,
        },
        "evidence": build_evidence(
            readme=readme,
            latest_plan=latest_plan,
            latest_spec=latest_spec,
            session_path=session_path,
            handover_path=handover_path,
            git_state=git_state,
            preferences_source=preferences_report["source"],
            workflow_source=workflow_report,
        ),
        "response_style": response_style,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Help/Next",
        f"- Status: {report['status']}",
        f"- Mode: {report['mode']}",
        f"- Workspace: {report['workspace']}",
        f"- Stage: {report['current_stage']}",
        f"- Focus: {report['current_focus']}",
        f"- Suggested workflow: {report['suggested_workflow']}",
        f"- Recommended action: {report['recommended_action']}",
    ]
    if report["alternatives"]:
        lines.append("- Alternatives:")
        for item in report["alternatives"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Alternatives: (none)")
    lines.append("- Evidence:")
    for item in report["evidence"]:
        lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Resolve a host-neutral help/next recommendation from workspace state.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root to inspect")
    parser.add_argument("--mode", choices=["help", "next"], required=True, help="Navigator mode")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve(), args.mode)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
