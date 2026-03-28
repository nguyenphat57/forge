from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from common import default_artifact_dir, slugify
from workflow_state_summary import as_string_list, summarize_workflow_state


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
        return {
            **common_fields,
            "label": report.get("chain", "Unnamed chain"),
            "status": report.get("status", "active"),
            "current_stage": report.get("current_stage", "unknown"),
            "next_steps": as_string_list(report.get("next_stages")),
            "blockers": as_string_list(report.get("blockers")),
            "risks": as_string_list(report.get("risks")),
            "gate_decision": report.get("gate_decision"),
        }
    if kind == "execution-progress":
        return {
            **common_fields,
            "label": report.get("task", "Unnamed task"),
            "status": report.get("status", "active"),
            "current_stage": report.get("stage", "unknown"),
            "completion_state": report.get("completion_state", "in-progress"),
            "next_steps": as_string_list(report.get("next")),
            "blockers": as_string_list(report.get("blockers")),
            "risks": as_string_list(report.get("risks")),
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
    return {
        **common_fields,
        "label": report.get("task", "Unnamed UI task"),
        "status": report.get("status", "active"),
        "current_stage": report.get("stage", "unknown"),
        "mode": report.get("mode", "frontend"),
        "next_steps": as_string_list(report.get("remaining_stages")),
        "notes": as_string_list(report.get("notes")),
    }


def _build_state(*, project: str, preferred_kind: str, latest_chain: dict | None, latest_execution: dict | None, latest_ui: dict | None, latest_run: dict | None, latest_gate: dict | None, updated_at: str) -> dict:
    return {
        "project": project,
        "updated_at": updated_at,
        "last_recorded_kind": preferred_kind,
        "latest_chain": latest_chain,
        "latest_execution": latest_execution,
        "latest_ui": latest_ui,
        "latest_run": latest_run,
        "latest_gate": latest_gate,
        "summary": summarize_workflow_state(
            latest_chain,
            latest_execution,
            latest_ui,
            latest_run,
            latest_gate,
            preferred_kind=preferred_kind,
        ),
    }


def record_workflow_event(kind: str, report: dict, *, output_dir: str | None = None, source_path: Path | None = None) -> tuple[Path, Path]:
    entry = _entry(kind, report, source_path)
    if entry is None:
        raise ValueError(f"Workflow event '{kind}' requires a JSON object report.")
    root = default_artifact_dir(output_dir, WORKFLOW_STATE_DIR) / slugify(str(entry.get("project", "workspace")))
    root.mkdir(parents=True, exist_ok=True)
    latest_path = root / "latest.json"
    current = _read_json_object(latest_path, "workflow state", []) if latest_path.exists() else {}
    state = _build_state(
        project=entry["project"],
        preferred_kind=kind,
        latest_chain=entry if kind == "chain-status" else current.get("latest_chain"),
        latest_execution=entry if kind == "execution-progress" else current.get("latest_execution"),
        latest_ui=entry if kind == "ui-progress" else current.get("latest_ui"),
        latest_run=entry if kind == "run-report" else current.get("latest_run"),
        latest_gate=entry if kind == "quality-gate" else current.get("latest_gate"),
        updated_at=entry["recorded_at"],
    )
    latest_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
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
    latest_path = _pick_latest_json(workspace / ".forge-artifacts" / WORKFLOW_STATE_DIR)
    if latest_path is not None:
        payload = _read_json_object(latest_path, "workflow state", local_warnings)
        if isinstance(payload, dict):
            return {"state": payload, "path": str(latest_path), "source": "workflow-state"}
    sources = {
        "execution-progress": _pick_latest_json(workspace / ".forge-artifacts" / "execution-progress"),
        "chain-status": _pick_latest_json(workspace / ".forge-artifacts" / "chain-status"),
        "ui-progress": _pick_latest_json(workspace / ".forge-artifacts" / "ui-progress"),
        "run-report": _pick_latest_json(workspace / ".forge-artifacts" / "run-reports"),
        "quality-gate": _pick_latest_json(workspace / ".forge-artifacts" / "quality-gates"),
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
        updated_at=_now_iso(),
    )
    project_entry = next((value for value in state.values() if isinstance(value, dict) and value.get("project")), None)
    if project_entry is not None:
        state["project"] = project_entry["project"]
    first_path = next((path for path in sources.values() if path is not None), None)
    return {"state": state, "path": str(first_path) if first_path else None, "source": "legacy-artifacts"}
