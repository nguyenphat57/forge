from __future__ import annotations

from workflow_state_io import string_list
from workflow_state_summary import summarize_workflow_state, workflow_hint_for_stage


def build_workflow_state(
    *,
    project: str,
    preferred_kind: str,
    latest_chain: dict | None,
    latest_execution: dict | None,
    latest_ui: dict | None,
    latest_run: dict | None,
    latest_gate: dict | None,
    latest_review: dict | None,
    latest_route_preview: dict | None,
    latest_direction: dict | None,
    latest_spec_review: dict | None,
    profile: str | None,
    intent: str | None,
    current_stage: str | None,
    required_stage_chain: list[str],
    stages: dict,
    updated_at: str,
) -> dict:
    return {
        "project": project,
        "updated_at": updated_at,
        "last_recorded_kind": preferred_kind,
        "profile": profile,
        "intent": intent,
        "current_stage": current_stage,
        "required_stage_chain": required_stage_chain,
        "stages": stages,
        "latest_chain": latest_chain,
        "latest_execution": latest_execution,
        "latest_ui": latest_ui,
        "latest_run": latest_run,
        "latest_gate": latest_gate,
        "latest_review": latest_review,
        "latest_route_preview": latest_route_preview,
        "latest_direction": latest_direction,
        "latest_spec_review": latest_spec_review,
        "summary": summarize_workflow_state(
            latest_chain,
            latest_execution,
            latest_ui,
            latest_run,
            latest_gate,
            latest_review,
            latest_route_preview,
            preferred_kind=preferred_kind,
        ),
    }


def build_packet_index(state: dict) -> dict:
    latest_execution = state.get("latest_execution") if isinstance(state.get("latest_execution"), dict) else {}
    latest_chain = state.get("latest_chain") if isinstance(state.get("latest_chain"), dict) else {}
    summary = state.get("summary") if isinstance(state.get("summary"), dict) else {}
    active_packets = string_list(latest_chain.get("active_packets"))
    packet_id = latest_execution.get("packet_id")
    if isinstance(packet_id, str) and packet_id.strip() and packet_id not in active_packets:
        active_packets = [packet_id, *active_packets]

    return {
        "project": state.get("project", "workspace"),
        "updated_at": state.get("updated_at"),
        "current_stage": state.get("current_stage"),
        "current_packet": packet_id if isinstance(packet_id, str) and packet_id.strip() else None,
        "packet_mode": latest_execution.get("packet_mode") if isinstance(latest_execution.get("packet_mode"), str) else None,
        "active_packets": active_packets,
        "blocked_packets": string_list(latest_chain.get("blocked_packets")),
        "review_ready_packets": string_list(latest_chain.get("review_ready_packets")),
        "merge_ready_packets": string_list(latest_chain.get("merge_ready_packets")),
        "browser_qa_pending": string_list(latest_chain.get("browser_qa_pending")),
        "merge_target": latest_execution.get("merge_target") or latest_chain.get("merge_target"),
        "next_merge_point": latest_chain.get("next_merge_point"),
        "summary": {
            "status": summary.get("status"),
            "primary_kind": summary.get("primary_kind"),
            "current_focus": summary.get("current_focus"),
            "recommended_action": summary.get("recommended_action"),
            "suggested_workflow": summary.get("suggested_workflow"),
        },
    }


def merge_browser_proof_into_execution(current_execution: dict | None, run_entry: dict | None) -> dict | None:
    if not isinstance(current_execution, dict) or not isinstance(run_entry, dict):
        return current_execution
    packet_id = run_entry.get("packet_id")
    browser_proof_status = run_entry.get("browser_proof_status")
    if not isinstance(packet_id, str) or not packet_id.strip():
        return current_execution
    if not isinstance(browser_proof_status, str) or not browser_proof_status.strip():
        return current_execution
    if current_execution.get("packet_id") != packet_id:
        return current_execution

    merged = dict(current_execution)
    merged["browser_qa_status"] = browser_proof_status
    result = run_entry.get("browser_proof_result")
    if isinstance(result, str) and result.strip():
        merged["browser_qa_last_result"] = result.strip()
    merged["browser_qa_last_recorded_at"] = run_entry.get("recorded_at")
    merged["browser_qa_last_source_path"] = run_entry.get("source_path")
    return merged


def refresh_loaded_summary(state: dict) -> dict:
    refreshed = dict(state)
    summary = refreshed.get("summary")
    if not isinstance(summary, dict):
        refreshed["summary"] = summarize_workflow_state(
            refreshed.get("latest_chain"),
            refreshed.get("latest_execution"),
            refreshed.get("latest_ui"),
            refreshed.get("latest_run"),
            refreshed.get("latest_gate"),
            refreshed.get("latest_review"),
            refreshed.get("latest_route_preview"),
            preferred_kind=refreshed.get("last_recorded_kind"),
        )
        return refreshed

    normalized_summary = dict(summary)
    primary_kind = normalized_summary.get("primary_kind")
    default_workflow = {
        "execution-progress": "build",
        "quality-gate": "review",
        "review-state": "review",
        "route-preview": "plan",
        "run-report": "test",
        "ui-progress": "session",
        "chain-status": "session",
    }.get(primary_kind, "session")
    normalized_summary["suggested_workflow"] = workflow_hint_for_stage(
        normalized_summary.get("suggested_workflow") or normalized_summary.get("current_stage") or refreshed.get("current_stage"),
        default=default_workflow,
    )
    refreshed["summary"] = normalized_summary
    return refreshed
