from __future__ import annotations

from pathlib import Path

from workflow_state_io import coalesce_list, coalesce_string, now_iso, string_list
from workflow_state_summary import as_string_list


def route_preview_detected(report: dict | None) -> dict:
    detected = report.get("detected") if isinstance(report, dict) else None
    return detected if isinstance(detected, dict) else {}


def route_preview_required_stage_chain(report: dict | None) -> list[str]:
    return string_list(route_preview_detected(report).get("required_stage_chain"))


def route_preview_current_stage(report: dict | None, fallback: str | None = None) -> str | None:
    detected = route_preview_detected(report)
    required_stages = detected.get("required_stages")
    if isinstance(required_stages, list):
        for item in required_stages:
            if not isinstance(item, dict):
                continue
            stage_name = item.get("stage")
            if not isinstance(stage_name, str) or not stage_name.strip():
                continue
            if item.get("status") != "skipped":
                return stage_name
    required_stage_chain = route_preview_required_stage_chain(report)
    return required_stage_chain[0] if required_stage_chain else fallback


def route_preview_stage_entries(report: dict | None, *, updated_at: str, source_path: Path | None) -> dict[str, dict]:
    detected = route_preview_detected(report)
    required_stages = detected.get("required_stages")
    if not isinstance(required_stages, list):
        return {}

    stages: dict[str, dict] = {}
    for item in required_stages:
        if not isinstance(item, dict):
            continue
        stage_name = item.get("stage")
        if not isinstance(stage_name, str) or not stage_name.strip():
            continue
        entry = {
            "status": item.get("status", "required"),
            "updated_at": updated_at,
            "source_path": str(source_path) if source_path else None,
        }
        for key in ("mode", "activation_reason", "skip_reason"):
            value = item.get(key)
            if value is not None:
                entry[key] = value
        stages[stage_name] = entry
    return stages

def workflow_entry(kind: str, report: dict | None, source_path: Path | None = None) -> dict | None:
    if not isinstance(report, dict):
        return None
    common_fields = {
        "kind": kind,
        "recorded_at": report.get("recorded_at") or report.get("updated_at") or now_iso(),
        "project": report.get("project", "workspace"),
        "source_path": str(source_path) if source_path else None,
    }

    if kind == "chain-status":
        write_scope_overlaps = coalesce_list(report, "write_scope_overlaps")
        review_ready_packets = coalesce_list(report, "review_ready_packets")
        merge_ready_packets = coalesce_list(report, "merge_ready_packets")
        review_readiness = coalesce_string(report, "review_readiness") or ("ready" if review_ready_packets else "pending")
        merge_readiness = coalesce_string(report, "merge_readiness") or ("ready" if merge_ready_packets else "pending")
        completion_gate = coalesce_string(report, "completion_gate") or (
            "merge-ready"
            if merge_readiness == "ready"
            else "review-ready"
            if review_readiness == "ready"
            else "blocked"
            if report.get("status") == "blocked" or report.get("gate_decision") == "blocked"
            else "incomplete"
        )
        return {
            **common_fields,
            "label": coalesce_string(report, "label", "chain") or "Unnamed chain",
            "status": report.get("status", "active"),
            "current_stage": report.get("current_stage", "unknown"),
            "next_steps": as_string_list(report.get("next_stages")),
            "active_packets": coalesce_list(report, "active_packets"),
            "blocked_packets": coalesce_list(report, "blocked_packets"),
            "review_ready_packets": review_ready_packets,
            "merge_ready_packets": merge_ready_packets,
            "browser_qa_pending": coalesce_list(report, "browser_qa_pending"),
            "write_scope_overlaps": write_scope_overlaps,
            "sequential_reasons": coalesce_list(report, "sequential_reasons"),
            "next_merge_point": coalesce_string(report, "next_merge_point"),
            "merge_target": coalesce_string(report, "merge_target"),
            "merge_strategy": coalesce_string(report, "merge_strategy") or "none",
            "overlap_risk_status": coalesce_string(report, "overlap_risk_status") or ("medium" if write_scope_overlaps else "none"),
            "review_readiness": review_readiness,
            "merge_readiness": merge_readiness,
            "completion_gate": completion_gate,
            "blockers": as_string_list(report.get("blockers")),
            "risks": as_string_list(report.get("risks")),
            "gate_decision": report.get("gate_decision"),
        }

    if kind == "execution-progress":
        write_scope_conflicts = coalesce_list(report, "write_scope_conflicts")
        review_readiness = coalesce_string(report, "review_readiness") or (
            "ready" if report.get("completion_state") in {"ready-for-review", "ready-for-merge"} else "pending"
        )
        merge_readiness = coalesce_string(report, "merge_readiness") or (
            "ready" if report.get("completion_state") == "ready-for-merge" else "pending"
        )
        completion_gate = coalesce_string(report, "completion_gate") or (
            "merge-ready"
            if merge_readiness == "ready"
            else "review-ready"
            if review_readiness == "ready"
            else "blocked"
            if report.get("status") == "blocked" or report.get("completion_state") == "blocked-by-residual-risk"
            else "incomplete"
        )
        return {
            **common_fields,
            "label": coalesce_string(report, "label", "task") or "Unnamed task",
            "packet_id": coalesce_string(report, "packet_id"),
            "packet_mode": coalesce_string(report, "packet_mode") or "standard",
            "parent_packet": coalesce_string(report, "parent_packet"),
            "goal": coalesce_string(report, "goal", "task") or "Unnamed task",
            "status": report.get("status", "active"),
            "current_stage": coalesce_string(report, "current_stage", "stage") or "unknown",
            "completion_state": report.get("completion_state", "in-progress"),
            "source_of_truth": coalesce_list(report, "source_of_truth", "source"),
            "exact_files_or_paths_in_scope": coalesce_list(report, "exact_files_or_paths_in_scope", "scope_paths", "scope_path"),
            "owned_files_or_write_scope": coalesce_list(report, "owned_files_or_write_scope", "owned_scope"),
            "depends_on_packets": coalesce_list(report, "depends_on_packets", "depends_on_packet"),
            "unblocks_packets": coalesce_list(report, "unblocks_packets", "unblock_packet"),
            "merge_target": coalesce_string(report, "merge_target"),
            "merge_strategy": coalesce_string(report, "merge_strategy") or "none",
            "overlap_risk_status": coalesce_string(report, "overlap_risk_status") or ("medium" if write_scope_conflicts else "none"),
            "write_scope_conflicts": write_scope_conflicts,
            "review_readiness": review_readiness,
            "merge_readiness": merge_readiness,
            "completion_gate": completion_gate,
            "baseline_or_clean_start_proof": coalesce_list(report, "baseline_or_clean_start_proof", "baseline_proof", "baseline"),
            "red_proof": coalesce_list(report, "red_proof"),
            "proof_before_progress": coalesce_list(report, "proof_before_progress", "proof"),
            "verification_to_rerun": coalesce_list(report, "verification_to_rerun", "verify_again"),
            "browser_qa_classification": coalesce_string(report, "browser_qa_classification") or "not-needed",
            "browser_qa_scope": coalesce_list(report, "browser_qa_scope"),
            "browser_qa_status": coalesce_string(report, "browser_qa_status") or "not-needed",
            "browser_qa_last_result": coalesce_string(report, "browser_qa_last_result"),
            "next_steps": coalesce_list(report, "next_steps", "next"),
            "blockers": as_string_list(report.get("blockers")),
            "residual_risk": coalesce_list(report, "residual_risk", "risks", "risk"),
        }

    if kind == "run-report":
        return {
            **common_fields,
            "label": report.get("command_display", "Unnamed command"),
            "status": report.get("status", "PASS"),
            "state": report.get("state", "completed"),
            "command_kind": report.get("command_kind", "generic"),
            "suggested_workflow": report.get("suggested_workflow"),
            "recommended_action": report.get("recommended_action"),
            "warnings": as_string_list(report.get("warnings")),
            "current_stage": report.get("current_stage"),
            "required_stage_chain": string_list(report.get("required_stage_chain")),
            "packet_id": coalesce_string(report, "packet_id"),
            "browser_proof_status": coalesce_string(report, "browser_proof_status"),
            "browser_proof_result": coalesce_string(report, "browser_proof_result"),
            "browser_proof_target": coalesce_string(report, "browser_proof_target"),
            "runtime_health_status": coalesce_string(report, "runtime_health_status"),
            "runtime_health_taxonomy": coalesce_string(report, "runtime_health_taxonomy"),
            "runtime_health_summary": coalesce_string(report, "runtime_health_summary"),
            "runtime_resolution_source": coalesce_string(report, "runtime_resolution_source"),
            "runtime_registry_path": coalesce_string(report, "runtime_registry_path"),
            "runtime_failure_taxonomy": coalesce_string(report, "runtime_failure_taxonomy"),
            "runtime_doctor_command": coalesce_string(report, "runtime_doctor_command"),
        }

    if kind == "quality-gate":
        return {
            **common_fields,
            "label": report.get("target_claim", "claim"),
            "profile": report.get("profile", "standard"),
            "decision": report.get("decision", "blocked"),
            "why": report.get("why", ""),
            "response": report.get("response", ""),
            "next_evidence": as_string_list(report.get("next_evidence")),
            "evidence_read": as_string_list(report.get("evidence_read")),
            "risks": as_string_list(report.get("risks")),
        }

    if kind == "review-state":
        return {
            **common_fields,
            "label": report.get("scope") or report.get("review_kind", "review"),
            "review_kind": report.get("review_kind", "quality-pass"),
            "disposition": report.get("disposition", "changes-required"),
            "branch_state": report.get("branch_state", "unknown"),
            "findings": as_string_list(report.get("findings")),
            "testing_gaps": as_string_list(report.get("testing_gaps")),
            "evidence": as_string_list(report.get("evidence")),
            "next_steps": as_string_list(report.get("next_actions")),
            "no_finding_rationale": report.get("no_finding_rationale"),
        }

    if kind == "direction-state":
        return {
            **common_fields,
            "label": report.get("summary", "direction"),
            "status": report.get("stage_status", "required"),
            "current_stage": report.get("stage_name", "brainstorm"),
            "mode": report.get("mode", "discovery-lite"),
            "decision_state": report.get("decision_state", "direction-locked"),
            "next_steps": as_string_list(report.get("next_actions")),
            "notes": as_string_list(report.get("notes")),
        }

    if kind == "spec-review-state":
        return {
            **common_fields,
            "label": report.get("summary", "spec-review"),
            "status": report.get("stage_status", "required"),
            "current_stage": report.get("stage_name", "spec-review"),
            "decision": report.get("decision", "go"),
            "next_steps": as_string_list(report.get("next_actions")),
            "notes": as_string_list(report.get("notes")),
        }

    if kind == "route-preview":
        detected = route_preview_detected(report)
        return {
            **common_fields,
            "label": report.get("prompt", "route-preview"),
            "status": "PASS",
            "current_stage": route_preview_current_stage(report, "plan"),
            "profile": detected.get("profile"),
            "intent": detected.get("intent"),
            "required_stage_chain": route_preview_required_stage_chain(report),
            "summary": report.get("activation_line"),
            "browser_qa_classification": detected.get("browser_qa_classification"),
            "browser_qa_scope": string_list(detected.get("browser_qa_scope")),
            "packet_mode": detected.get("packet_mode"),
        }

    if kind == "stage-state":
        stage_name = report.get("stage_name") or report.get("current_stage") or "unknown"
        return {
            **common_fields,
            "label": report.get("summary") or stage_name,
            "status": report.get("stage_status", "active"),
            "current_stage": stage_name,
            "next_steps": as_string_list(report.get("next_actions")),
            "notes": as_string_list(report.get("notes")),
        }

    return {
        **common_fields,
        "label": report.get("task", "Unnamed UI task"),
        "status": report.get("status", "active"),
        "current_stage": report.get("stage", "unknown"),
        "mode": report.get("mode", "frontend"),
        "next_steps": as_string_list(report.get("remaining_stages")),
        "notes": as_string_list(report.get("notes")),
    }
