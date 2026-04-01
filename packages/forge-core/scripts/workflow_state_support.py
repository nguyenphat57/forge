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


def _string_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


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
            "current_stage": report.get("current_stage"),
            "required_stage_chain": _string_list(report.get("required_stage_chain")),
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
    state = _build_state(
        project=entry["project"],
        preferred_kind=kind,
        latest_chain=entry if kind == "chain-status" else current.get("latest_chain"),
        latest_execution=entry if kind == "execution-progress" else current.get("latest_execution"),
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
