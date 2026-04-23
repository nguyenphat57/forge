from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, slugify
from workflow_state_bootstrap_support import seed_workflow_state_from_sidecars
from workflow_stage_machine import (
    current_stage_after_transition,
    seed_required_stages,
    stage_entry,
    transition_entry,
    validate_transition,
)
from workflow_state_io import pick_latest_named_json, read_json_object, string_list
from workflow_state_projection import (
    build_packet_index,
    build_workflow_state,
    latest_entries_from_state,
    merge_browser_proof_into_execution,
    refresh_loaded_summary,
    route_preview_detected,
    route_preview_required_stage_chain,
    route_preview_stage_entries,
    workflow_entry,
)


WORKFLOW_STATE_DIR = "workflow-state"
EVENT_RETENTION = 200


def _event_root(output_dir: str | None, project: str) -> Path:
    root = default_artifact_dir(output_dir, WORKFLOW_STATE_DIR) / slugify(project)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _merge_stage_snapshot(stages: dict, stage_snapshot: tuple[str, dict] | None) -> dict:
    merged = dict(stages) if isinstance(stages, dict) else {}
    if stage_snapshot is None:
        return merged
    stage_name, snapshot = stage_snapshot
    existing = merged.get(stage_name, {})
    merged[stage_name] = {**existing, **snapshot}
    return merged


def _required_stage_chain(kind: str, report: dict, current: dict) -> list[str]:
    if kind == "legacy-spec-review-state":
        return ["plan", "build"]
    required_stage_chain = string_list(report.get("required_stage_chain"))
    if not required_stage_chain and kind == "route-preview":
        required_stage_chain = route_preview_required_stage_chain(report)
    if not required_stage_chain:
        required_stage_chain = string_list(current.get("required_stage_chain"))
    return required_stage_chain


def record_workflow_event(kind: str, report: dict, *, output_dir: str | None = None, source_path: Path | None = None) -> tuple[Path, Path]:
    entry = workflow_entry(kind, report, source_path)
    transition = transition_entry(kind, report, str(source_path) if source_path else None)
    if entry is None and transition is None:
        raise ValueError(f"Workflow event '{kind}' requires a JSON object report.")

    project = (
        str((entry or {}).get("project") or report.get("project") or "workspace")
        if isinstance(report, dict)
        else "workspace"
    )
    root = _event_root(output_dir, project)
    latest_path = root / "latest.json"
    current_payload = read_json_object(latest_path, "workflow state", []) if latest_path.exists() else {}
    current = refresh_loaded_summary(current_payload) if isinstance(current_payload, dict) else {}

    if transition is not None:
        validate_transition(current, transition)

    recorded_at = (
        str((entry or {}).get("recorded_at") or (transition or {}).get("recorded_at") or report.get("recorded_at"))
        if isinstance(report, dict)
        else None
    )
    required_stage_chain = _required_stage_chain(kind, report, current) if isinstance(report, dict) else []

    stages = seed_required_stages(
        current.get("stages") if isinstance(current.get("stages"), dict) else {},
        required_stage_chain,
        recorded_at or current.get("updated_at") or "",
    )
    if kind == "route-preview":
        preview_recorded_at = str((entry or {}).get("recorded_at") or report.get("recorded_at"))
        for stage_name, snapshot in route_preview_stage_entries(
            report,
            updated_at=preview_recorded_at,
            source_path=source_path,
        ).items():
            existing = stages.get(stage_name, {})
            stages[stage_name] = {**existing, **snapshot}
    stages = _merge_stage_snapshot(stages, stage_entry(kind, report, source_path))

    current_stage = current_stage_after_transition(
        current.get("current_stage"),
        required_stage_chain,
        stages,
        transition,
    )
    profile = report.get("operating_profile") or report.get("profile") or current.get("profile") if isinstance(report, dict) else current.get("profile")
    intent = report.get("intent") or current.get("intent") if isinstance(report, dict) else current.get("intent")
    if kind == "route-preview":
        detected = route_preview_detected(report)
        profile = detected.get("profile") or profile
        intent = detected.get("intent") or intent

    latest_execution = entry if kind == "execution-progress" else current.get("latest_execution")
    if kind == "run-report":
        latest_execution = merge_browser_proof_into_execution(latest_execution, entry)

    latest_entries = latest_entries_from_state(current)
    latest_entries.update(
        {
            "latest_chain": entry if kind == "chain-status" else latest_entries.get("latest_chain"),
            "latest_execution": latest_execution,
            "latest_ui": entry if kind == "ui-progress" else latest_entries.get("latest_ui"),
            "latest_run": entry if kind == "run-report" else latest_entries.get("latest_run"),
            "latest_gate": entry if kind == "quality-gate" else latest_entries.get("latest_gate"),
            "latest_review": entry if kind == "review-state" else latest_entries.get("latest_review"),
            "latest_route_preview": entry if kind == "route-preview" else latest_entries.get("latest_route_preview"),
            "latest_direction": entry if kind == "direction-state" else latest_entries.get("latest_direction"),
        }
    )

    state = build_workflow_state(
        project=project,
        preferred_kind=kind,
        latest_entries=latest_entries,
        profile=profile,
        intent=intent,
        current_stage=current_stage,
        required_stage_chain=required_stage_chain,
        stages=stages,
        last_transition=transition or current.get("last_transition"),
        updated_at=str((entry or {}).get("recorded_at") or (transition or {}).get("recorded_at") or current.get("updated_at")),
    )
    packet_index = build_packet_index(state)
    state["packet_index"] = packet_index
    latest_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    packet_index_path = root / "packet-index.json"
    packet_index_path.write_text(json.dumps(packet_index, indent=2, ensure_ascii=False), encoding="utf-8")

    events_path = root / "events.jsonl"
    event = {
        "kind": kind,
        "label": (entry or {}).get("label") or project,
        "project": project,
        "recorded_at": (entry or {}).get("recorded_at") or (transition or {}).get("recorded_at"),
        "source_path": (entry or {}).get("source_path") or (transition or {}).get("source_path"),
        "stage_name": (transition or {}).get("stage_name"),
        "stage_status": (transition or {}).get("stage_status"),
        "transition_id": (transition or {}).get("transition_id"),
    }
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    lines = events_path.read_text(encoding="utf-8").splitlines()
    if len(lines) > EVENT_RETENTION:
        events_path.write_text("\n".join(lines[-EVENT_RETENTION:]) + "\n", encoding="utf-8")
    return latest_path, events_path


def resolve_workflow_state(
    workspace: Path,
    warnings: list[str] | None = None,
    *,
    auto_seed_missing: bool = False,
) -> dict:
    local_warnings = warnings if warnings is not None else []
    workflow_root = workspace / ".forge-artifacts" / WORKFLOW_STATE_DIR
    latest_path = pick_latest_named_json(workflow_root, "latest.json")
    packet_index_path = pick_latest_named_json(workflow_root, "packet-index.json")

    if latest_path is not None:
        payload = read_json_object(latest_path, "workflow state", local_warnings)
        if isinstance(payload, dict):
            refreshed = refresh_loaded_summary(payload)
            if not isinstance(refreshed.get("packet_index"), dict):
                packet_index_payload = read_json_object(packet_index_path, "packet index", local_warnings) if packet_index_path else None
                refreshed["packet_index"] = packet_index_payload if isinstance(packet_index_payload, dict) else build_packet_index(refreshed)
            return {"state": refreshed, "path": str(latest_path), "source": "workflow-state"}
        if packet_index_path is not None:
            local_warnings.append("Ignored packet-index because canonical workflow-state root is missing or invalid.")
        return {"state": None, "path": None, "source": None}

    if auto_seed_missing and seed_workflow_state_from_sidecars(workspace, local_warnings, record_event=record_workflow_event) is not None:
        return resolve_workflow_state(workspace, local_warnings, auto_seed_missing=False)

    if packet_index_path is not None:
        local_warnings.append("Ignored packet-index because canonical workflow-state root is not seeded yet.")
    return {"state": None, "path": None, "source": None}
