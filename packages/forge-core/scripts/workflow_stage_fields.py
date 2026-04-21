from __future__ import annotations

from workflow_state_io import coalesce_list, coalesce_string, now_iso, string_list
from workflow_state_summary import as_string_list
from workflow_state_entries import route_preview_current_stage, route_preview_required_stage_chain


VALID_STAGE_STATUSES = ("pending", "required", "active", "completed", "skipped", "blocked")


def stage_name_for(kind: str, report: dict | None) -> str | None:
    if not isinstance(report, dict):
        return None
    if kind == "legacy-spec-review-state":
        decision = report.get("decision")
        status = report.get("stage_status")
        return "build" if decision == "go" and status == "completed" else "plan"
    explicit = report.get("stage_name")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if kind == "direction-state":
        return "brainstorm"
    if kind == "quality-gate":
        return "quality-gate"
    if kind == "review-state":
        return "self-review"
    if kind == "execution-progress":
        value = report.get("current_stage") or report.get("stage")
        return value.strip() if isinstance(value, str) and value.strip() else None
    if kind == "ui-progress":
        value = report.get("stage") or report.get("current_stage")
        return value.strip() if isinstance(value, str) and value.strip() else None
    if kind == "route-preview":
        return route_preview_current_stage(report)
    return None


def stage_status_for(kind: str, report: dict | None) -> str | None:
    if not isinstance(report, dict):
        return None
    explicit = report.get("stage_status")
    if isinstance(explicit, str) and explicit in VALID_STAGE_STATUSES:
        return explicit
    if kind == "execution-progress":
        status = report.get("status")
        completion_state = report.get("completion_state")
        if status == "blocked" or completion_state == "blocked-by-residual-risk":
            return "blocked"
        if status == "completed" or completion_state in {"ready-for-review", "ready-for-merge"}:
            return "completed"
        return "active"
    if kind == "quality-gate":
        decision = report.get("decision")
        if decision == "go":
            return "completed"
        if decision in {"conditional", "blocked"}:
            return "blocked"
    status = report.get("status")
    if status == "blocked":
        return "blocked"
    if status == "completed":
        return "completed"
    if kind == "route-preview":
        return "active"
    return None


def transition_id_for(kind: str, report: dict, stage_name: str, recorded_at: str) -> str:
    explicit = report.get("transition_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if kind == "execution-progress":
        packet_id = report.get("packet_id")
        if isinstance(packet_id, str) and packet_id.strip():
            return f"{kind}:{stage_name}:{packet_id.strip()}:{recorded_at}"
    return f"{kind}:{stage_name}:{recorded_at}"


def artifact_refs(report: dict) -> list[str]:
    refs = [item.strip() for item in report.get("artifact_refs", []) if isinstance(item, str) and item.strip()] if isinstance(report.get("artifact_refs"), list) else []
    singular = report.get("artifact")
    if isinstance(singular, str) and singular.strip():
        refs.append(singular.strip())
    for group_name in ("process_artifacts", "review_artifacts"):
        group = report.get(group_name)
        if not isinstance(group, list):
            continue
        for item in group:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if isinstance(path, str) and path.strip():
                refs.append(path.strip())
    seen: set[str] = set()
    merged: list[str] = []
    for item in refs:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return merged


def evidence_refs(report: dict) -> list[str]:
    refs: list[str] = []
    if isinstance(report.get("evidence_refs"), list):
        refs.extend(item.strip() for item in report["evidence_refs"] if isinstance(item, str) and item.strip())
    refs.extend(as_string_list(report.get("evidence")))
    refs.extend(as_string_list(report.get("evidence_read")))
    refs.extend(coalesce_list(report, "proof_before_progress", "proof"))
    refs.extend(coalesce_list(report, "verification_to_rerun"))
    if isinstance(report.get("post_deploy_verification"), list):
        refs.extend(item.strip() for item in report["post_deploy_verification"] if isinstance(item, str) and item.strip())
    seen: set[str] = set()
    merged: list[str] = []
    for item in refs:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return merged


def transition_entry(kind: str, report: dict | None, source_path: str | None) -> dict | None:
    if not isinstance(report, dict):
        return None
    stage_name = stage_name_for(kind, report)
    stage_status = stage_status_for(kind, report)
    if not isinstance(stage_name, str) or not stage_name.strip():
        return None
    if not isinstance(stage_status, str) or stage_status not in VALID_STAGE_STATUSES:
        return None
    recorded_at = report.get("recorded_at") or report.get("updated_at") or now_iso()
    transition = {
        "kind": kind,
        "stage_name": stage_name,
        "stage_status": stage_status,
        "recorded_at": recorded_at,
        "transition_id": transition_id_for(kind, report, stage_name, recorded_at),
        "source_path": source_path,
        "event_ref": source_path,
        "required_stage_chain": ["plan", "build"]
        if kind == "legacy-spec-review-state"
        else string_list(report.get("required_stage_chain"))
        if kind != "route-preview"
        else route_preview_required_stage_chain(report),
        "summary": coalesce_string(report, "summary"),
        "activation_reason": coalesce_string(report, "activation_reason"),
        "skip_reason": coalesce_string(report, "skip_reason"),
        "decision": coalesce_string(report, "decision", "decision_state"),
        "disposition": coalesce_string(report, "disposition"),
        "target": coalesce_string(report, "target", "target_claim"),
        "release_artifact_id": coalesce_string(report, "release_artifact_id"),
        "rollback_path": coalesce_string(report, "rollback_path"),
        "next_stage_override": coalesce_string(report, "next_stage_override"),
        "expected_previous_stage": coalesce_string(report, "expected_previous_stage"),
        "profile": coalesce_string(report, "operating_profile", "profile"),
        "intent": coalesce_string(report, "intent"),
        "artifact_refs": artifact_refs(report),
        "evidence_refs": evidence_refs(report),
        "notes": as_string_list(report.get("notes")),
        "next_actions": as_string_list(report.get("next_actions")) or as_string_list(report.get("next_steps")),
        "post_deploy_verification": [item.strip() for item in report.get("post_deploy_verification", []) if isinstance(item, str) and item.strip()] if isinstance(report.get("post_deploy_verification"), list) else [],
    }
    return transition
