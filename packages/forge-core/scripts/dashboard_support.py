from __future__ import annotations

import json
from pathlib import Path

from companion_operator_context import collect_operator_context
from companion_matching import match_companions
from help_next_support import (
    adoption_signal_label,
    build_evidence,
    build_focus,
    build_recommendations,
    collect_repo_signals,
    determine_stage,
    extract_markdown_title,
    find_latest_json,
    find_latest_markdown,
    find_latest_named_file,
    release_tier_label,
    read_git_status,
    read_json_object,
)
from runtime_tool_support import available_runtime_tool_names, resolve_runtime_tool
from workflow_state_support import resolve_workflow_state


def _load_json_array_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    return len(payload) if isinstance(payload, list) else 0


def _active_change(workspace: Path, warnings: list[str]) -> dict | None:
    latest_path = find_latest_named_file(workspace, ".forge-artifacts/changes/active", "status.json")
    if latest_path is None:
        return None
    payload = read_json_object(latest_path, "active change status", warnings)
    if not isinstance(payload, dict):
        return None
    payload["path"] = str(latest_path)
    return payload


def _latest_release_report(workspace: Path, category: str, warnings: list[str]) -> dict | None:
    latest_path = find_latest_json(workspace, f".forge-artifacts/{category}")
    if latest_path is None:
        return None
    payload = read_json_object(latest_path, category, warnings)
    if not isinstance(payload, dict):
        return None
    payload["path"] = str(latest_path)
    return payload


def _latest_verification(workflow_state: dict | None, active_change: dict | None) -> dict | None:
    if isinstance(workflow_state, dict):
        for key, kind in (("latest_gate", "quality-gate"), ("latest_review", "review-state"), ("latest_run", "run-report")):
            item = workflow_state.get(key)
            if isinstance(item, dict):
                if kind == "quality-gate":
                    status = item.get("decision")
                elif kind == "review-state":
                    status = item.get("disposition")
                else:
                    status = item.get("status")
                return {
                    "kind": kind,
                    "label": item.get("label"),
                    "status": status,
                    "path": item.get("source_path"),
                }
    if isinstance(active_change, dict):
        verification = active_change.get("verification")
        if isinstance(verification, dict) and verification.get("latest_result"):
            return {
                "kind": "change-verification",
                "label": active_change.get("summary"),
                "status": verification.get("latest_result"),
                "path": active_change.get("path"),
            }
    return None


def build_dashboard_report(workspace: Path) -> dict:
    warnings: list[str] = []
    readme = next((candidate for candidate in (workspace / "README.md", workspace / "README") if candidate.exists()), None)
    session_path = workspace / ".brain" / "session.json"
    session = read_json_object(session_path, "session", warnings) if session_path.exists() else None
    latest_plan = find_latest_markdown(workspace, "docs/plans")
    latest_spec = find_latest_markdown(workspace, "docs/specs")
    codebase_summary = workspace / ".forge-artifacts" / "codebase" / "summary.md"
    codebase_path = codebase_summary if codebase_summary.exists() else None
    workflow_source = resolve_workflow_state(workspace, warnings)
    workflow_state = workflow_source.get("state")
    active_change = _active_change(workspace, warnings)
    git_state = read_git_status(workspace)
    release_readiness = _latest_release_report(workspace, "release-readiness", warnings)
    adoption_check = _latest_release_report(workspace, "adoption-check", warnings)
    stage = determine_stage(
        session=session,
        git_state=git_state,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        workflow_state=workflow_state,
        codebase_summary=codebase_path,
        active_change=active_change,
    )
    focus = build_focus(
        stage,
        session=session,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        git_state=git_state,
        workflow_state=workflow_state,
        codebase_summary=codebase_path,
        active_change=active_change,
        release_readiness=release_readiness,
        latest_adoption_check=adoption_check,
    )
    next_workflow, recommended_action, alternatives = build_recommendations(
        mode="help",
        stage=stage,
        session=session,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        handover_excerpt=None,
        workflow_state=workflow_state,
        codebase_summary=codebase_path,
        active_change=active_change,
        release_readiness=release_readiness,
        latest_adoption_check=adoption_check,
    )
    latest_verification = _latest_verification(workflow_state, active_change)
    latest_gate = (workflow_state or {}).get("latest_gate") if isinstance(workflow_state, dict) else None
    if not isinstance(latest_gate, dict) and isinstance(latest_verification, dict) and latest_verification.get("kind") == "quality-gate":
        latest_gate = latest_verification
    runtime_tools = [resolve_runtime_tool(bundle_name) for bundle_name in available_runtime_tool_names()]
    companions = match_companions(workspace=workspace)
    operator_context = {item["id"]: item for item in collect_operator_context(companions, workspace)}
    release_doc_sync = _latest_release_report(workspace, "release-doc-sync", warnings)
    workspace_canary = _latest_release_report(workspace, "workspace-canaries", warnings)
    release_readiness = _latest_release_report(workspace, "release-readiness", warnings)
    brownfield = {
        "mapped": codebase_path is not None,
        "planned": bool(latest_plan or latest_spec),
        "active_change": active_change is not None,
    }
    report = {
        "status": "PASS",
        "workspace": str(workspace),
        "current_stage": stage,
        "stage": stage,
        "focus": focus,
        "next_workflow": next_workflow,
        "recommended_action": recommended_action,
        "alternatives": alternatives,
        "evidence": build_evidence(
            readme=readme,
            latest_plan=latest_plan,
            latest_spec=latest_spec,
            session_path=session_path if session_path.exists() else None,
            handover_path=None,
            git_state=git_state,
            preferences_source={"path": None},
            workflow_source=workflow_source,
            codebase_summary=codebase_path,
        ),
        "session": {
            "path": str(session_path) if session_path.exists() else None,
            "task": ((session or {}).get("working_on") or {}).get("task") or ((session or {}).get("working_on") or {}).get("feature"),
            "pending_tasks": (session or {}).get("pending_tasks", []),
        },
        "continuity": {
            "decisions": _load_json_array_count(workspace / ".brain" / "decisions.json"),
            "learnings": _load_json_array_count(workspace / ".brain" / "learnings.json"),
        },
        "plan": {"path": str(latest_plan) if latest_plan else None, "title": extract_markdown_title(latest_plan)},
        "spec": {"path": str(latest_spec) if latest_spec else None, "title": extract_markdown_title(latest_spec)},
        "codebase": {"path": str(codebase_path) if codebase_path else None},
        "brownfield": brownfield,
        "active_change": active_change,
        "workflow_state": {"path": workflow_source.get("path"), "summary": (workflow_state or {}).get("summary")},
        "release_tier": release_tier_label(release_readiness),
        "latest_gate": latest_gate,
        "latest_adoption_signal": adoption_signal_label(adoption_check),
        "latest_verification": latest_verification,
        "repo_signals": collect_repo_signals(workspace),
        "git": git_state,
        "runtime_tools": runtime_tools,
        "companions": [
            {
                "id": item["id"],
                "strength": item["strength"],
                "features": sorted(key for key, matched in item["features"].items() if matched),
                "profile": operator_context.get(item["id"], {}).get("profile"),
                "verification_pack": operator_context.get(item["id"], {}).get("verification_pack"),
            }
            for item in companions
        ],
        "release": {
            "release_doc_sync": release_doc_sync,
            "workspace_canary": workspace_canary,
            "release_readiness": release_readiness,
            "latest_adoption_check": adoption_check,
        },
        "warnings": warnings,
    }
    return report


def format_dashboard_text(report: dict) -> str:
    lines = [
        "Forge Dashboard",
        f"- Workspace: {report['workspace']}",
        f"- Current stage: {report['current_stage']}",
        f"- Release tier: {report.get('release_tier') or '(none)'}",
        f"- Focus: {report['focus']}",
        f"- Next workflow: {report['next_workflow']}",
        f"- Recommended action: {report['recommended_action']}",
        f"- Session task: {report['session']['task'] or '(none)'}",
        f"- Pending tasks: {len(report['session']['pending_tasks'])}",
        f"- Decisions: {report['continuity']['decisions']}",
        f"- Learnings: {report['continuity']['learnings']}",
        f"- Plan: {report['plan']['title'] or '(none)'}",
        f"- Spec: {report['spec']['title'] or '(none)'}",
        f"- Codebase map: {'ready' if report['brownfield']['mapped'] else 'missing'}",
        f"- Latest gate: {(report.get('latest_gate') or {}).get('decision') or (report['latest_verification'] or {}).get('kind') or '(none)'}",
        f"- Latest adoption signal: {report.get('latest_adoption_signal') or '(none)'}",
        f"- Latest verification: {(report['latest_verification'] or {}).get('kind') or '(none)'}",
        f"- Optional companions: {', '.join(item['id'] for item in report['companions']) or '(none)'}",
        "- Runtime tools:",
    ]
    if report["companions"]:
        lines.append("- Optional companion context:")
        for item in report["companions"]:
            lines.append(f"  - {item['id']}: profile={item.get('profile') or '(none)'}, pack={item.get('verification_pack') or '(none)'}")
    for item in report["runtime_tools"]:
        detail = item.get("target") or item.get("error") or "(none)"
        lines.append(f"  - {item['bundle']}: [{item['status']}] {detail}")
    release = report["release"]
    lines.append("- Release state:")
    for key in ("release_doc_sync", "workspace_canary", "release_readiness"):
        item = release.get(key)
        label = key.replace("_", " ")
        status = item.get("status") if isinstance(item, dict) else None
        summary = item.get("summary") if isinstance(item, dict) else None
        lines.append(f"  - {label}: {status or '(none)'}{f' | {summary}' if summary else ''}")
    adoption_item = release.get("latest_adoption_check")
    if isinstance(adoption_item, dict):
        lines.append(
            f"  - latest adoption check: {adoption_item.get('impact') or '(none)'} | {adoption_item.get('summary') or adoption_item.get('label') or '(none)'}"
        )
    if report["alternatives"]:
        lines.append("- Alternatives:")
        for item in report["alternatives"]:
            lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)
