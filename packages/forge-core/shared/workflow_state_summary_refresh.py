from __future__ import annotations

from workflow_state_canonical import (
    SCHEMA_VERSION,
    canonical_chain,
    canonical_stage_summary,
    normalize_summary_workflow,
    normalized_last_transition,
)
from workflow_state_io import string_list
from workflow_state_summary import summarize_workflow_state


LATEST_ENTRY_FIELDS = (
    "latest_chain",
    "latest_execution",
    "latest_ui",
    "latest_run",
    "latest_gate",
    "latest_review",
    "latest_route_preview",
    "latest_direction",
)


def latest_entries_from_state(state: dict | None) -> dict[str, dict | None]:
    payload = state if isinstance(state, dict) else {}
    return {field: payload.get(field) if isinstance(payload.get(field), dict) else None for field in LATEST_ENTRY_FIELDS}


def _summary_from_latest_entries(latest_entries: dict[str, dict | None], *, preferred_kind: str | None) -> dict:
    return summarize_workflow_state(
        latest_entries.get("latest_chain"),
        latest_entries.get("latest_execution"),
        latest_entries.get("latest_ui"),
        latest_entries.get("latest_run"),
        latest_entries.get("latest_gate"),
        latest_entries.get("latest_review"),
        latest_entries.get("latest_route_preview"),
        preferred_kind=preferred_kind,
    )


def build_workflow_state(
    *,
    project: str,
    preferred_kind: str,
    latest_entries: dict[str, dict | None],
    profile: str | None,
    intent: str | None,
    current_stage: str | None,
    required_stage_chain: list[str],
    stages: dict,
    last_transition: dict | None,
    updated_at: str,
) -> dict:
    normalized_latest_entries = latest_entries_from_state(latest_entries)
    summary = _summary_from_latest_entries(normalized_latest_entries, preferred_kind=preferred_kind)
    canonical_summary = canonical_stage_summary(
        last_transition,
        current_stage=current_stage,
        required_stage_chain=required_stage_chain,
        stages=stages if isinstance(stages, dict) else {},
    )
    if preferred_kind == "stage-state" and canonical_summary is not None:
        summary = canonical_summary
    elif isinstance(summary, dict) and summary.get("status") == "empty" and canonical_summary is not None:
        summary = canonical_summary
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "updated_at": updated_at,
        "last_recorded_kind": preferred_kind,
        "profile": profile,
        "intent": intent,
        "current_stage": current_stage,
        "required_stage_chain": required_stage_chain,
        "stages": stages,
        "last_transition": last_transition,
        **normalized_latest_entries,
        "summary": summary,
    }


def build_packet_index(state: dict) -> dict:
    latest_entries = latest_entries_from_state(state)
    latest_execution = latest_entries["latest_execution"] or {}
    latest_chain = latest_entries["latest_chain"] or {}
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
    refreshed["schema_version"] = (
        refreshed.get("schema_version")
        if isinstance(refreshed.get("schema_version"), int) and refreshed.get("schema_version") >= 1
        else SCHEMA_VERSION
    )
    refreshed["last_transition"] = normalized_last_transition(refreshed)

    summary = refreshed.get("summary")
    if not isinstance(summary, dict):
        refreshed["summary"] = _summary_from_latest_entries(
            latest_entries_from_state(refreshed),
            preferred_kind=refreshed.get("last_recorded_kind"),
        )
    else:
        refreshed["summary"] = normalize_summary_workflow(summary, refreshed.get("current_stage"))

    canonical_summary = canonical_stage_summary(
        refreshed.get("last_transition"),
        current_stage=refreshed.get("current_stage"),
        required_stage_chain=canonical_chain(refreshed),
        stages=refreshed.get("stages") if isinstance(refreshed.get("stages"), dict) else {},
    )
    if canonical_summary is not None and (
        refreshed.get("last_recorded_kind") == "stage-state"
        or refreshed["summary"].get("status") == "empty"
    ):
        refreshed["summary"] = canonical_summary

    refreshed["summary"] = normalize_summary_workflow(refreshed["summary"], refreshed.get("current_stage"))
    return refreshed
