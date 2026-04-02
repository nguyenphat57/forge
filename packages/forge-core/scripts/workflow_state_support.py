from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from common import default_artifact_dir, slugify
from workflow_state_summary import as_string_list, summarize_workflow_state, workflow_hint_for_stage


WORKFLOW_STATE_DIR = "workflow-state"
EVENT_RETENTION = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json_object(path: Path, label: str, warnings: list[str]) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warnings.append(f"Invalid JSON in {label}: {path}.")
        return None
    return payload if isinstance(payload, dict) else None


def _mtime_rank(path: Path) -> tuple[float, str]:
    try:
        return path.stat().st_mtime, str(path).lower()
    except OSError:
        return float("-inf"), ""


def _pick_latest_json(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob("*.json"):
        rank = _mtime_rank(candidate)
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def _pick_latest_named_json(base_dir: Path, filename: str) -> Path | None:
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob(filename):
        rank = _mtime_rank(candidate)
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def _string_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def _coalesce_string(report: dict, *keys: str) -> str | None:
    for key in keys:
        value = report.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _coalesce_list(report: dict, *keys: str) -> list[str]:
    for key in keys:
        value = report.get(key)
        values = _string_list(value)
        if values:
            return values
    return []


def _route_preview_detected(report: dict | None) -> dict:
    detected = report.get("detected") if isinstance(report, dict) else None
    return detected if isinstance(detected, dict) else {}


def _route_preview_required_stage_chain(report: dict | None) -> list[str]:
    return _string_list(_route_preview_detected(report).get("required_stage_chain"))


def _route_preview_current_stage(report: dict | None, fallback: str | None = None) -> str | None:
    detected = _route_preview_detected(report)
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
    required_stage_chain = _route_preview_required_stage_chain(report)
    return required_stage_chain[0] if required_stage_chain else fallback


def _route_preview_stage_entries(report: dict | None, *, updated_at: str, source_path: Path | None) -> dict[str, dict]:
    detected = _route_preview_detected(report)
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


def _stage_entry(kind: str, report: dict, source_path: Path | None = None) -> tuple[str, dict] | None:
    stage_name = report.get("stage_name")
    if not isinstance(stage_name, str) or not stage_name.strip():
        return None
    entry = {
        "status": report.get("stage_status", "required"),
        "updated_at": report.get("recorded_at") or report.get("updated_at") or _now_iso(),
        "source_path": str(source_path) if source_path else None,
    }
    for key in (
        "mode",
        "activation_reason",
        "skip_reason",
        "artifact",
        "decision",
        "decision_state",
        "target",
        "summary",
    ):
        value = report.get(key)
        if value is not None:
            entry[key] = value
    if kind == "direction-state":
        entry["decision_state"] = report.get("decision_state")
    if kind == "spec-review-state":
        entry["decision"] = report.get("decision")
        entry["review_iteration"] = report.get("review_iteration")
        entry["max_review_iterations"] = report.get("max_review_iterations")
    if kind == "adoption-check":
        entry["signals"] = _string_list(report.get("signals"))
        entry["next_actions"] = _string_list(report.get("next_actions"))
        entry["impact"] = report.get("impact")
        entry["confidence"] = report.get("confidence")
        entry["evidence_sources"] = _string_list(report.get("evidence_sources"))
        entry["frictions"] = _string_list(report.get("frictions"))
        entry["friction_categories"] = _string_list(report.get("friction_categories"))
        entry["release_actions"] = _string_list(report.get("release_actions"))
        entry["metrics"] = _string_list(report.get("metrics"))
    return stage_name, entry


def _entry(kind: str, report: dict | None, source_path: Path | None = None) -> dict | None:
    if not isinstance(report, dict):
        return None
    common_fields = {
        "kind": kind,
        "recorded_at": report.get("recorded_at") or report.get("updated_at") or _now_iso(),
        "project": report.get("project", "workspace"),
        "source_path": str(source_path) if source_path else None,
    }
    if kind == "chain-status":
        write_scope_overlaps = _coalesce_list(report, "write_scope_overlaps")
        review_ready_packets = _coalesce_list(report, "review_ready_packets")
        merge_ready_packets = _coalesce_list(report, "merge_ready_packets")
        review_readiness = _coalesce_string(report, "review_readiness") or ("ready" if review_ready_packets else "pending")
        merge_readiness = _coalesce_string(report, "merge_readiness") or ("ready" if merge_ready_packets else "pending")
        completion_gate = _coalesce_string(report, "completion_gate") or (
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
            "label": _coalesce_string(report, "label", "chain") or "Unnamed chain",
            "status": report.get("status", "active"),
            "current_stage": report.get("current_stage", "unknown"),
            "next_steps": as_string_list(report.get("next_stages")),
            "active_packets": _coalesce_list(report, "active_packets"),
            "blocked_packets": _coalesce_list(report, "blocked_packets"),
            "review_ready_packets": review_ready_packets,
            "merge_ready_packets": merge_ready_packets,
            "browser_qa_pending": _coalesce_list(report, "browser_qa_pending"),
            "write_scope_overlaps": write_scope_overlaps,
            "sequential_reasons": _coalesce_list(report, "sequential_reasons"),
            "next_merge_point": _coalesce_string(report, "next_merge_point"),
            "merge_target": _coalesce_string(report, "merge_target"),
            "merge_strategy": _coalesce_string(report, "merge_strategy") or "none",
            "overlap_risk_status": _coalesce_string(report, "overlap_risk_status") or ("medium" if write_scope_overlaps else "none"),
            "review_readiness": review_readiness,
            "merge_readiness": merge_readiness,
            "completion_gate": completion_gate,
            "blockers": as_string_list(report.get("blockers")),
            "risks": as_string_list(report.get("risks")),
            "gate_decision": report.get("gate_decision"),
        }
    if kind == "execution-progress":
        write_scope_conflicts = _coalesce_list(report, "write_scope_conflicts")
        review_readiness = _coalesce_string(report, "review_readiness") or (
            "ready" if report.get("completion_state") in {"ready-for-review", "ready-for-merge"} else "pending"
        )
        merge_readiness = _coalesce_string(report, "merge_readiness") or (
            "ready" if report.get("completion_state") == "ready-for-merge" else "pending"
        )
        completion_gate = _coalesce_string(report, "completion_gate") or (
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
            "label": _coalesce_string(report, "label", "task") or "Unnamed task",
            "packet_id": _coalesce_string(report, "packet_id"),
            "packet_mode": _coalesce_string(report, "packet_mode") or "standard",
            "parent_packet": _coalesce_string(report, "parent_packet"),
            "goal": _coalesce_string(report, "goal", "task") or "Unnamed task",
            "status": report.get("status", "active"),
            "current_stage": _coalesce_string(report, "current_stage", "stage") or "unknown",
            "completion_state": report.get("completion_state", "in-progress"),
            "source_of_truth": _coalesce_list(report, "source_of_truth", "source"),
            "exact_files_or_paths_in_scope": _coalesce_list(report, "exact_files_or_paths_in_scope", "scope_paths", "scope_path"),
            "owned_files_or_write_scope": _coalesce_list(report, "owned_files_or_write_scope", "owned_scope"),
            "depends_on_packets": _coalesce_list(report, "depends_on_packets", "depends_on_packet"),
            "unblocks_packets": _coalesce_list(report, "unblocks_packets", "unblock_packet"),
            "merge_target": _coalesce_string(report, "merge_target"),
            "merge_strategy": _coalesce_string(report, "merge_strategy") or "none",
            "overlap_risk_status": _coalesce_string(report, "overlap_risk_status") or ("medium" if write_scope_conflicts else "none"),
            "write_scope_conflicts": write_scope_conflicts,
            "review_readiness": review_readiness,
            "merge_readiness": merge_readiness,
            "completion_gate": completion_gate,
            "baseline_or_clean_start_proof": _coalesce_list(report, "baseline_or_clean_start_proof", "baseline_proof", "baseline"),
            "red_proof": _coalesce_list(report, "red_proof"),
            "proof_before_progress": _coalesce_list(report, "proof_before_progress", "proof"),
            "verification_to_rerun": _coalesce_list(report, "verification_to_rerun", "verify_again"),
            "browser_qa_classification": _coalesce_string(report, "browser_qa_classification") or "not-needed",
            "browser_qa_scope": _coalesce_list(report, "browser_qa_scope"),
            "browser_qa_status": _coalesce_string(report, "browser_qa_status") or "not-needed",
            "browser_qa_last_result": _coalesce_string(report, "browser_qa_last_result"),
            "next_steps": _coalesce_list(report, "next_steps", "next"),
            "blockers": as_string_list(report.get("blockers")),
            "residual_risk": _coalesce_list(report, "residual_risk", "risks", "risk"),
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
            "required_stage_chain": _string_list(report.get("required_stage_chain")),
            "packet_id": _coalesce_string(report, "packet_id"),
            "browser_proof_status": _coalesce_string(report, "browser_proof_status"),
            "browser_proof_result": _coalesce_string(report, "browser_proof_result"),
            "browser_proof_target": _coalesce_string(report, "browser_proof_target"),
            "runtime_health_status": _coalesce_string(report, "runtime_health_status"),
            "runtime_health_taxonomy": _coalesce_string(report, "runtime_health_taxonomy"),
            "runtime_health_summary": _coalesce_string(report, "runtime_health_summary"),
            "runtime_resolution_source": _coalesce_string(report, "runtime_resolution_source"),
            "runtime_registry_path": _coalesce_string(report, "runtime_registry_path"),
            "runtime_failure_taxonomy": _coalesce_string(report, "runtime_failure_taxonomy"),
            "runtime_doctor_command": _coalesce_string(report, "runtime_doctor_command"),
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
    if kind == "adoption-check":
        return {
            **common_fields,
            "label": report.get("summary", "adoption-check"),
            "status": report.get("stage_status", "completed"),
            "current_stage": report.get("stage_name", "adoption-check"),
            "target": report.get("target", "unknown"),
            "next_steps": as_string_list(report.get("next_actions")),
            "notes": as_string_list(report.get("signals")),
            "impact": report.get("impact", "neutral"),
            "confidence": report.get("confidence", "medium"),
            "evidence_sources": as_string_list(report.get("evidence_sources")),
            "frictions": as_string_list(report.get("frictions")),
            "friction_categories": as_string_list(report.get("friction_categories")),
            "release_actions": as_string_list(report.get("release_actions")),
            "metrics": as_string_list(report.get("metrics")),
        }
    if kind == "route-preview":
        detected = _route_preview_detected(report)
        return {
            **common_fields,
            "label": report.get("prompt", "route-preview"),
            "status": "PASS",
            "current_stage": _route_preview_current_stage(report, "mapped"),
            "profile": detected.get("profile"),
            "intent": detected.get("intent"),
            "required_stage_chain": _route_preview_required_stage_chain(report),
            "summary": report.get("activation_line"),
            "browser_qa_classification": detected.get("browser_qa_classification"),
            "browser_qa_scope": _string_list(detected.get("browser_qa_scope")),
            "packet_mode": detected.get("packet_mode"),
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


def _build_state(
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
    latest_adoption_check: dict | None,
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
        "latest_adoption_check": latest_adoption_check,
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


def _build_packet_index(state: dict) -> dict:
    latest_execution = state.get("latest_execution") if isinstance(state.get("latest_execution"), dict) else {}
    latest_chain = state.get("latest_chain") if isinstance(state.get("latest_chain"), dict) else {}
    summary = state.get("summary") if isinstance(state.get("summary"), dict) else {}
    active_packets = _string_list(latest_chain.get("active_packets"))
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
        "blocked_packets": _string_list(latest_chain.get("blocked_packets")),
        "review_ready_packets": _string_list(latest_chain.get("review_ready_packets")),
        "merge_ready_packets": _string_list(latest_chain.get("merge_ready_packets")),
        "browser_qa_pending": _string_list(latest_chain.get("browser_qa_pending")),
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


def _merge_browser_proof_into_execution(current_execution: dict | None, run_entry: dict | None) -> dict | None:
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


def _refresh_loaded_summary(state: dict) -> dict:
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


def record_workflow_event(kind: str, report: dict, *, output_dir: str | None = None, source_path: Path | None = None) -> tuple[Path, Path]:
    entry = _entry(kind, report, source_path)
    if entry is None:
        raise ValueError(f"Workflow event '{kind}' requires a JSON object report.")
    root = default_artifact_dir(output_dir, WORKFLOW_STATE_DIR) / slugify(str(entry.get("project", "workspace")))
    root.mkdir(parents=True, exist_ok=True)
    latest_path = root / "latest.json"
    current = _read_json_object(latest_path, "workflow state", []) if latest_path.exists() else {}
    stages = dict(current.get("stages", {})) if isinstance(current.get("stages"), dict) else {}
    required_stage_chain = _string_list(report.get("required_stage_chain")) or _string_list(current.get("required_stage_chain"))
    if not required_stage_chain and kind == "route-preview":
        required_stage_chain = _route_preview_required_stage_chain(report)
    for stage_name in required_stage_chain:
        existing = stages.get(stage_name)
        if isinstance(existing, dict):
            continue
        stages[stage_name] = {
            "status": "required",
            "updated_at": entry["recorded_at"],
            "source_path": None,
        }
    if kind == "route-preview":
        for stage_name, snapshot in _route_preview_stage_entries(
            report,
            updated_at=entry["recorded_at"],
            source_path=source_path,
        ).items():
            existing = stages.get(stage_name, {})
            stages[stage_name] = {**existing, **snapshot}
    stage_snapshot = _stage_entry(kind, report, source_path)
    if stage_snapshot is not None:
        stage_name, snapshot = stage_snapshot
        existing = stages.get(stage_name, {})
        stages[stage_name] = {**existing, **snapshot}
    current_stage = report.get("current_stage")
    profile = report.get("operating_profile") or report.get("profile")
    intent = report.get("intent")
    if kind == "route-preview" and not current_stage:
        current_stage = _route_preview_current_stage(report, current.get("current_stage"))
    if kind == "route-preview":
        detected = _route_preview_detected(report)
        profile = detected.get("profile") or profile
        intent = detected.get("intent") or intent
    latest_execution = entry if kind == "execution-progress" else current.get("latest_execution")
    if kind == "run-report":
        latest_execution = _merge_browser_proof_into_execution(latest_execution, entry)
    state = _build_state(
        project=entry["project"],
        preferred_kind=kind,
        latest_chain=entry if kind == "chain-status" else current.get("latest_chain"),
        latest_execution=latest_execution,
        latest_ui=entry if kind == "ui-progress" else current.get("latest_ui"),
        latest_run=entry if kind == "run-report" else current.get("latest_run"),
        latest_gate=entry if kind == "quality-gate" else current.get("latest_gate"),
        latest_review=entry if kind == "review-state" else current.get("latest_review"),
        latest_route_preview=entry if kind == "route-preview" else current.get("latest_route_preview"),
        latest_direction=entry if kind == "direction-state" else current.get("latest_direction"),
        latest_spec_review=entry if kind == "spec-review-state" else current.get("latest_spec_review"),
        latest_adoption_check=entry if kind == "adoption-check" else current.get("latest_adoption_check"),
        profile=profile or current.get("profile"),
        intent=intent or current.get("intent"),
        current_stage=current_stage or (stage_snapshot[0] if stage_snapshot else current.get("current_stage")),
        required_stage_chain=required_stage_chain,
        stages=stages,
        updated_at=entry["recorded_at"],
    )
    packet_index = _build_packet_index(state)
    state["packet_index"] = packet_index
    latest_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    packet_index_path = root / "packet-index.json"
    packet_index_path.write_text(json.dumps(packet_index, indent=2, ensure_ascii=False), encoding="utf-8")
    events_path = root / "events.jsonl"
    event = {"kind": kind, "label": entry["label"], "project": entry["project"], "recorded_at": entry["recorded_at"], "source_path": entry["source_path"]}
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    lines = events_path.read_text(encoding="utf-8").splitlines()
    if len(lines) > EVENT_RETENTION:
        events_path.write_text("\n".join(lines[-EVENT_RETENTION:]) + "\n", encoding="utf-8")
    return latest_path, events_path


def resolve_workflow_state(workspace: Path, warnings: list[str] | None = None) -> dict:
    local_warnings = warnings if warnings is not None else []
    workflow_root = workspace / ".forge-artifacts" / WORKFLOW_STATE_DIR
    latest_path = _pick_latest_named_json(workflow_root, "latest.json")
    packet_index_path = _pick_latest_named_json(workflow_root, "packet-index.json")
    if latest_path is not None:
        payload = _read_json_object(latest_path, "workflow state", local_warnings)
        if isinstance(payload, dict):
            refreshed = _refresh_loaded_summary(payload)
            if not isinstance(refreshed.get("packet_index"), dict):
                packet_index_payload = _read_json_object(packet_index_path, "packet index", local_warnings) if packet_index_path else None
                refreshed["packet_index"] = (
                    packet_index_payload
                    if isinstance(packet_index_payload, dict)
                    else _build_packet_index(refreshed)
                )
            return {"state": refreshed, "path": str(latest_path), "source": "workflow-state"}

    if packet_index_path is not None:
        packet_index_payload = _read_json_object(packet_index_path, "packet index", local_warnings)
        if isinstance(packet_index_payload, dict):
            state = {
                "project": packet_index_payload.get("project", "workspace"),
                "updated_at": packet_index_payload.get("updated_at"),
                "last_recorded_kind": "packet-index",
                "current_stage": packet_index_payload.get("current_stage"),
                "required_stage_chain": [],
                "stages": {},
                "latest_chain": None,
                "latest_execution": None,
                "latest_ui": None,
                "latest_run": None,
                "latest_gate": None,
                "latest_review": None,
                "latest_route_preview": None,
                "latest_direction": None,
                "latest_spec_review": None,
                "latest_adoption_check": None,
                "packet_index": packet_index_payload,
                "summary": packet_index_payload.get("summary", {}),
            }
            return {"state": _refresh_loaded_summary(state), "path": str(packet_index_path), "source": "packet-index"}

    sources = {
        "execution-progress": _pick_latest_json(workspace / ".forge-artifacts" / "execution-progress"),
        "chain-status": _pick_latest_json(workspace / ".forge-artifacts" / "chain-status"),
        "ui-progress": _pick_latest_json(workspace / ".forge-artifacts" / "ui-progress"),
        "run-report": _pick_latest_json(workspace / ".forge-artifacts" / "run-reports"),
        "quality-gate": _pick_latest_json(workspace / ".forge-artifacts" / "quality-gates"),
        "review-state": _pick_latest_json(workspace / ".forge-artifacts" / "reviews"),
        "route-preview": _pick_latest_json(workspace / ".forge-artifacts" / "route-previews"),
        "direction-state": _pick_latest_json(workspace / ".forge-artifacts" / "direction"),
        "spec-review-state": _pick_latest_json(workspace / ".forge-artifacts" / "spec-review"),
        "adoption-check": _pick_latest_json(workspace / ".forge-artifacts" / "adoption-check"),
    }
    if not any(sources.values()):
        return {"state": None, "path": None, "source": None}
    preferred_kind = max(sources.items(), key=lambda item: _mtime_rank(item[1]) if item[1] else (float("-inf"), ""))[0]
    state = _build_state(
        project="workspace",
        preferred_kind=preferred_kind,
        latest_chain=_entry("chain-status", _read_json_object(sources["chain-status"], "chain status", local_warnings), sources["chain-status"]),
        latest_execution=_entry("execution-progress", _read_json_object(sources["execution-progress"], "execution progress", local_warnings), sources["execution-progress"]),
        latest_ui=_entry("ui-progress", _read_json_object(sources["ui-progress"], "ui progress", local_warnings), sources["ui-progress"]),
        latest_run=_entry("run-report", _read_json_object(sources["run-report"], "run report", local_warnings), sources["run-report"]),
        latest_gate=_entry("quality-gate", _read_json_object(sources["quality-gate"], "quality gate", local_warnings), sources["quality-gate"]),
        latest_review=_entry("review-state", _read_json_object(sources["review-state"], "review state", local_warnings), sources["review-state"]),
        latest_route_preview=_entry("route-preview", _read_json_object(sources["route-preview"], "route preview", local_warnings), sources["route-preview"]),
        latest_direction=_entry("direction-state", _read_json_object(sources["direction-state"], "direction state", local_warnings), sources["direction-state"]),
        latest_spec_review=_entry("spec-review-state", _read_json_object(sources["spec-review-state"], "spec review state", local_warnings), sources["spec-review-state"]),
        latest_adoption_check=_entry("adoption-check", _read_json_object(sources["adoption-check"], "adoption check", local_warnings), sources["adoption-check"]),
        profile=None,
        intent=None,
        current_stage=None,
        required_stage_chain=[],
        stages={},
        updated_at=_now_iso(),
    )
    project_entry = next((value for value in state.values() if isinstance(value, dict) and value.get("project")), None)
    if project_entry is not None:
        state["project"] = project_entry["project"]
    first_path = next((path for path in sources.values() if path is not None), None)
    return {"state": state, "path": str(first_path) if first_path else None, "source": "legacy-artifacts"}
