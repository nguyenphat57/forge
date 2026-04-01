from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, load_preferences, resolve_response_style
from help_next_support import (
    adoption_signal_label,
    build_evidence,
    build_focus,
    build_recommendations,
    collect_repo_signals,
    determine_stage,
    extract_markdown_title,
    find_latest_markdown,
    find_latest_json,
    find_latest_named_file,
    first_existing_file,
    release_tier_label,
    read_git_status,
    read_handover_excerpt,
    read_json_object,
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
    codebase_summary = workspace / ".forge-artifacts" / "codebase" / "summary.md"
    codebase_summary = codebase_summary if codebase_summary.exists() else None
    active_change_path = find_latest_named_file(workspace, ".forge-artifacts/changes/active", "status.json")
    active_change = read_json_object(active_change_path, "active change status", warnings) if active_change_path else None
    session_path = workspace / ".brain" / "session.json"
    session = read_json_object(session_path, "session context", warnings)
    handover_path = workspace / ".brain" / "handover.md"
    handover_excerpt = read_handover_excerpt(handover_path)
    git_state = read_git_status(workspace)
    repo_signals = collect_repo_signals(workspace)
    workflow_report = resolve_workflow_state(workspace, warnings)
    workflow_state = workflow_report["state"]
    release_readiness_path = find_latest_json(workspace, ".forge-artifacts/release-readiness")
    release_readiness = read_json_object(release_readiness_path, "release-readiness", warnings) if release_readiness_path else None
    latest_adoption_path = find_latest_json(workspace, ".forge-artifacts/adoption-check")
    latest_adoption_check = read_json_object(latest_adoption_path, "adoption-check", warnings) if latest_adoption_path else None

    stage = determine_stage(
        session=session,
        git_state=git_state,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        workflow_state=workflow_state,
        codebase_summary=codebase_summary,
        active_change=active_change,
    )
    if stage == "unscoped":
        warnings.append("No session context found.")
        warnings.append("No active plan or spec found.")

    focus = build_focus(
        stage,
        session=session,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        git_state=git_state,
        workflow_state=workflow_state,
        codebase_summary=codebase_summary,
        active_change=active_change,
        release_readiness=release_readiness,
        latest_adoption_check=latest_adoption_check,
    )
    suggested_workflow, recommended_action, alternatives = build_recommendations(
        mode=mode,
        stage=stage,
        session=session,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        handover_excerpt=handover_excerpt,
        workflow_state=workflow_state,
        codebase_summary=codebase_summary,
        active_change=active_change,
        release_readiness=release_readiness,
        latest_adoption_check=latest_adoption_check,
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
            "codebase_summary": str(codebase_summary) if codebase_summary else None,
            "active_change_status": str(active_change_path) if active_change_path else None,
            "workflow_state_file": workflow_report["path"],
            "workflow_state_source": workflow_report["source"],
            "workflow_summary": workflow_state.get("summary") if isinstance(workflow_state, dict) else None,
            "release_readiness_file": str(release_readiness_path) if release_readiness_path else None,
            "release_tier": release_tier_label(release_readiness),
            "release_readiness_tier": release_tier_label(release_readiness),
            "latest_adoption_check_file": str(latest_adoption_path) if latest_adoption_path else None,
            "latest_adoption_signal": adoption_signal_label(latest_adoption_check),
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
            codebase_summary=codebase_summary,
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
