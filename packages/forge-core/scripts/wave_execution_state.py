from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, slugify
from workflow_state_io import now_iso, read_json_object


WAVE_PLAN_FILENAME = "wave-plan.json"


def workflow_state_root(workspace: Path, project_name: str) -> Path:
    root = default_artifact_dir(str(workspace.resolve()), "workflow-state") / slugify(project_name)
    root.mkdir(parents=True, exist_ok=True)
    return root


def wave_plan_path(workspace: Path, project_name: str) -> Path:
    return workflow_state_root(workspace, project_name) / WAVE_PLAN_FILENAME


def load_packet_file(packet_file: Path) -> list[dict]:
    payload = json.loads(packet_file.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    packets = payload.get("packets") if isinstance(payload, dict) else None
    if not isinstance(packets, list):
        raise ValueError(f"Wave packet file must contain a list or a 'packets' array: {packet_file}")
    return [item for item in packets if isinstance(item, dict)]


def load_wave_plan(workspace: Path, project_name: str) -> dict:
    warnings: list[str] = []
    payload = read_json_object(wave_plan_path(workspace, project_name), "wave plan", warnings)
    if warnings:
        raise ValueError(warnings[0])
    if not isinstance(payload, dict):
        raise ValueError(f"Missing wave plan for project '{project_name}'.")
    return payload


def save_wave_plan(plan: dict, workspace: Path, project_name: str) -> Path:
    path = wave_plan_path(workspace, project_name)
    payload = dict(plan)
    payload["project"] = project_name
    payload["updated_at"] = now_iso()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_latest_execution_progress(workspace: Path, project_name: str) -> dict[str, dict]:
    root = default_artifact_dir(str(workspace.resolve()), "execution-progress") / slugify(project_name)
    if not root.exists():
        return {}
    reports: list[Path] = sorted(root.rglob("*.json"), key=lambda candidate: (candidate.stat().st_mtime, str(candidate).lower()), reverse=True)
    latest: dict[str, dict] = {}
    for path in reports:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        packet_id = payload.get("packet_id")
        if not isinstance(packet_id, str) or not packet_id.strip() or packet_id in latest:
            continue
        payload["_artifact_path"] = str(path)
        payload["_artifact_mtime"] = path.stat().st_mtime
        latest[packet_id] = payload
    return latest


def load_latest_run_reports(workspace: Path, project_name: str) -> dict[str, dict]:
    root = default_artifact_dir(str(workspace.resolve()), "run-reports")
    if not root.exists():
        return {}
    reports: list[Path] = sorted(root.rglob("*.json"), key=lambda candidate: (candidate.stat().st_mtime, str(candidate).lower()), reverse=True)
    latest: dict[str, dict] = {}
    for path in reports:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("project") != project_name:
            continue
        command_display = payload.get("command_display")
        if not isinstance(command_display, str) or not command_display.strip() or command_display in latest:
            continue
        payload["_artifact_path"] = str(path)
        payload["_artifact_mtime"] = path.stat().st_mtime
        latest[command_display] = payload
    return latest


def build_wave_chain_report(plan: dict, project_name: str) -> dict:
    ready_packets = list(plan.get("ready_packets", []))
    running_packets = list(plan.get("running_packets", []))
    blocked_packets = list(plan.get("blocked_packets", []))
    completed_packets = list(plan.get("completed_packets", []))
    current_wave = plan.get("current_wave")
    wave_count = plan.get("wave_count", len(plan.get("waves", [])))
    merge_target = plan.get("merge_target")
    shared_verification_pending = list(plan.get("shared_verification_pending", []))
    shared_verification_status = str(plan.get("shared_verification_status") or ("pending" if shared_verification_pending else "not-needed"))
    status = "blocked" if blocked_packets and not ready_packets and not running_packets else "completed" if current_wave is None else "active"
    if shared_verification_status == "pending":
        current_stage = "test"
    else:
        current_stage = "review" if current_wave is None and merge_target else "build"
    return {
        "chain": "Wave execution",
        "label": f"Wave execution: {project_name}",
        "project": project_name,
        "status": status,
        "current_stage": current_stage,
        "next_stages": ["review"] if current_stage == "review" else ["build"],
        "active_packets": running_packets or ready_packets,
        "ready_packets": ready_packets,
        "running_packets": running_packets,
        "completed_packets": completed_packets,
        "blocked_packets": blocked_packets,
        "current_wave_blocked_packets": list(plan.get("current_wave_blocked_packets", [])),
        "review_ready_packets": [],
        "merge_ready_packets": [],
        "browser_qa_pending": [],
        "write_scope_overlaps": [],
        "sequential_reasons": [],
        "wave_plan_id": plan.get("wave_plan_id"),
        "wave_index": current_wave,
        "wave_count": wave_count,
        "next_ready_wave": list((plan.get("next_ready_wave") or {}).get("packet_ids", [])),
        "next_merge_point": plan.get("next_merge_point"),
        "merge_target": merge_target,
        "merge_strategy": plan.get("merge_strategy") or "none",
        "review_readiness": "ready" if current_stage == "review" else "pending",
        "merge_readiness": "ready" if current_stage == "review" and merge_target else "pending",
        "completion_gate": "merge-ready" if current_stage == "review" and merge_target else "blocked" if status == "blocked" else "incomplete",
        "shared_verification": list(plan.get("shared_verification", [])),
        "shared_verification_status": shared_verification_status,
        "shared_verification_pending": shared_verification_pending,
        "blockers": [f"Blocked packet: {packet_id}" for packet_id in blocked_packets],
        "risks": [],
    }


def persist_wave_plan_and_state(plan: dict, workspace: Path, project_name: str) -> Path:
    path = save_wave_plan(plan, workspace, project_name)
    from workflow_state_support import record_workflow_event

    record_workflow_event(
        "chain-status",
        build_wave_chain_report(plan, project_name),
        output_dir=str(workspace.resolve()),
        source_path=path,
    )
    return path
