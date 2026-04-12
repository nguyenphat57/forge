from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, slugify
from workflow_state_io import mtime_rank, now_iso, pick_latest_json, pick_latest_named_json, read_json_object, string_list
from workflow_state_projection import (
    build_packet_index,
    build_workflow_state,
    merge_browser_proof_into_execution,
    refresh_loaded_summary,
    route_preview_current_stage,
    route_preview_detected,
    route_preview_required_stage_chain,
    route_preview_stage_entries,
    stage_entry,
    workflow_entry,
)


WORKFLOW_STATE_DIR = "workflow-state"
EVENT_RETENTION = 200


def record_workflow_event(kind: str, report: dict, *, output_dir: str | None = None, source_path: Path | None = None) -> tuple[Path, Path]:
    entry = workflow_entry(kind, report, source_path)
    if entry is None:
        raise ValueError(f"Workflow event '{kind}' requires a JSON object report.")

    root = default_artifact_dir(output_dir, WORKFLOW_STATE_DIR) / slugify(str(entry.get("project", "workspace")))
    root.mkdir(parents=True, exist_ok=True)
    latest_path = root / "latest.json"
    current = read_json_object(latest_path, "workflow state", []) if latest_path.exists() else {}
    stages = dict(current.get("stages", {})) if isinstance(current.get("stages"), dict) else {}
    required_stage_chain = string_list(report.get("required_stage_chain")) or string_list(current.get("required_stage_chain"))

    if not required_stage_chain and kind == "route-preview":
        required_stage_chain = route_preview_required_stage_chain(report)
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
        for stage_name, snapshot in route_preview_stage_entries(
            report,
            updated_at=entry["recorded_at"],
            source_path=source_path,
        ).items():
            existing = stages.get(stage_name, {})
            stages[stage_name] = {**existing, **snapshot}

    stage_snapshot = stage_entry(kind, report, source_path)
    if stage_snapshot is not None:
        stage_name, snapshot = stage_snapshot
        existing = stages.get(stage_name, {})
        stages[stage_name] = {**existing, **snapshot}

    current_stage = report.get("current_stage")
    profile = report.get("operating_profile") or report.get("profile")
    intent = report.get("intent")
    if kind == "route-preview" and not current_stage:
        current_stage = route_preview_current_stage(report, current.get("current_stage"))
    if kind == "route-preview":
        detected = route_preview_detected(report)
        profile = detected.get("profile") or profile
        intent = detected.get("intent") or intent

    latest_execution = entry if kind == "execution-progress" else current.get("latest_execution")
    if kind == "run-report":
        latest_execution = merge_browser_proof_into_execution(latest_execution, entry)

    state = build_workflow_state(
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
        profile=profile or current.get("profile"),
        intent=intent or current.get("intent"),
        current_stage=current_stage or (stage_snapshot[0] if stage_snapshot else current.get("current_stage")),
        required_stage_chain=required_stage_chain,
        stages=stages,
        updated_at=entry["recorded_at"],
    )
    packet_index = build_packet_index(state)
    state["packet_index"] = packet_index
    latest_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    packet_index_path = root / "packet-index.json"
    packet_index_path.write_text(json.dumps(packet_index, indent=2, ensure_ascii=False), encoding="utf-8")

    events_path = root / "events.jsonl"
    event = {
        "kind": kind,
        "label": entry["label"],
        "project": entry["project"],
        "recorded_at": entry["recorded_at"],
        "source_path": entry["source_path"],
    }
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    lines = events_path.read_text(encoding="utf-8").splitlines()
    if len(lines) > EVENT_RETENTION:
        events_path.write_text("\n".join(lines[-EVENT_RETENTION:]) + "\n", encoding="utf-8")
    return latest_path, events_path


def resolve_workflow_state(workspace: Path, warnings: list[str] | None = None) -> dict:
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
        packet_index_payload = read_json_object(packet_index_path, "packet index", local_warnings)
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
                "packet_index": packet_index_payload,
                "summary": packet_index_payload.get("summary", {}),
            }
            return {"state": refresh_loaded_summary(state), "path": str(packet_index_path), "source": "packet-index"}

    sources = {
        "execution-progress": pick_latest_json(workspace / ".forge-artifacts" / "execution-progress"),
        "chain-status": pick_latest_json(workspace / ".forge-artifacts" / "chain-status"),
        "ui-progress": pick_latest_json(workspace / ".forge-artifacts" / "ui-progress"),
        "run-report": pick_latest_json(workspace / ".forge-artifacts" / "run-reports"),
        "quality-gate": pick_latest_json(workspace / ".forge-artifacts" / "quality-gates"),
        "review-state": pick_latest_json(workspace / ".forge-artifacts" / "reviews"),
        "route-preview": pick_latest_json(workspace / ".forge-artifacts" / "route-previews"),
        "direction-state": pick_latest_json(workspace / ".forge-artifacts" / "direction"),
        "spec-review-state": pick_latest_json(workspace / ".forge-artifacts" / "spec-review"),
    }
    if not any(sources.values()):
        return {"state": None, "path": None, "source": None}

    preferred_kind = max(
        sources.items(),
        key=lambda item: mtime_rank(item[1]) if item[1] else (float("-inf"), ""),
    )[0]

    state = build_workflow_state(
        project="workspace",
        preferred_kind=preferred_kind,
        latest_chain=workflow_entry("chain-status", read_json_object(sources["chain-status"], "chain status", local_warnings), sources["chain-status"]),
        latest_execution=workflow_entry("execution-progress", read_json_object(sources["execution-progress"], "execution progress", local_warnings), sources["execution-progress"]),
        latest_ui=workflow_entry("ui-progress", read_json_object(sources["ui-progress"], "ui progress", local_warnings), sources["ui-progress"]),
        latest_run=workflow_entry("run-report", read_json_object(sources["run-report"], "run report", local_warnings), sources["run-report"]),
        latest_gate=workflow_entry("quality-gate", read_json_object(sources["quality-gate"], "quality gate", local_warnings), sources["quality-gate"]),
        latest_review=workflow_entry("review-state", read_json_object(sources["review-state"], "review state", local_warnings), sources["review-state"]),
        latest_route_preview=workflow_entry("route-preview", read_json_object(sources["route-preview"], "route preview", local_warnings), sources["route-preview"]),
        latest_direction=workflow_entry("direction-state", read_json_object(sources["direction-state"], "direction state", local_warnings), sources["direction-state"]),
        latest_spec_review=workflow_entry("spec-review-state", read_json_object(sources["spec-review-state"], "spec review state", local_warnings), sources["spec-review-state"]),
        profile=None,
        intent=None,
        current_stage=None,
        required_stage_chain=[],
        stages={},
        updated_at=now_iso(),
    )
    project_entry = next((value for value in state.values() if isinstance(value, dict) and value.get("project")), None)
    if project_entry is not None:
        state["project"] = project_entry["project"]
    first_path = next((path for path in sources.values() if path is not None), None)
    return {"state": state, "path": str(first_path) if first_path else None, "source": "legacy-artifacts"}
