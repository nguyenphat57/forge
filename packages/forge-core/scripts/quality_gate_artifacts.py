from __future__ import annotations

import json
from pathlib import Path

from common import load_registry
from workflow_state_support import resolve_workflow_state


TARGETS_REQUIRING_PROCESS_ARTIFACT = {"done", "ready-for-review", "ready-for-merge", "deploy"}
TARGETS_REQUIRING_REVIEW_ARTIFACT = {"ready-for-merge", "done", "deploy"}
TARGETS_REQUIRING_VERIFY_CHANGE = {"ready-for-merge", "done", "deploy"}
VALID_COMPLETED_STAGE_STATUSES = {"completed", "skipped"}


def _mtime_rank(path: Path | None) -> tuple[float, str]:
    if path is None:
        return float("-inf"), ""
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


def _pick_latest_named(base_dir: Path, filename: str) -> Path | None:
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


def _read_json_object(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _artifact_ref(kind: str, path: Path, payload: dict, *, summary_key: str, state_key: str) -> dict:
    return {
        "kind": kind,
        "path": str(path),
        "summary": payload.get(summary_key),
        "state": payload.get(state_key),
    }


def _validate_required_stage_state(workspace: Path, decision: str) -> None:
    if decision != "go":
        return
    workflow_state = resolve_workflow_state(workspace).get("state")
    if not isinstance(workflow_state, dict):
        return
    stages = workflow_state.get("stages")
    if not isinstance(stages, dict) or not stages:
        return
    required_stage_chain = workflow_state.get("required_stage_chain")
    stage_names = [name for name in required_stage_chain if isinstance(name, str)] if isinstance(required_stage_chain, list) else []
    if "quality-gate" in stage_names:
        stage_names = stage_names[: stage_names.index("quality-gate")]
    elif not stage_names:
        stage_names = [name for name, payload in stages.items() if isinstance(payload, dict)]
    valid_skip_reasons = set(load_registry().get("solo_profiles", {}).get("skip_reasons", []))
    pending: list[str] = []
    for stage_name in stage_names:
        payload = stages.get(stage_name)
        if not isinstance(payload, dict):
            pending.append(stage_name)
            continue
        status = payload.get("status")
        if status == "completed":
            continue
        if status == "skipped" and payload.get("skip_reason") in valid_skip_reasons:
            continue
        pending.append(stage_name)
    if pending:
        raise ValueError(
            "Quality gate cannot return 'go' while required stages are incomplete: {0}.".format(", ".join(pending))
        )


def collect_process_artifacts(workspace: Path) -> tuple[list[dict], dict]:
    artifacts: list[dict] = []
    latest_execution: dict | None = None
    latest_change: dict | None = None
    latest_verify_change: dict | None = None

    change_path = _pick_latest_named(workspace / ".forge-artifacts" / "changes" / "active", "status.json")
    change_payload = _read_json_object(change_path)
    if change_path is not None and isinstance(change_payload, dict):
        latest_change = change_payload
        artifacts.append(_artifact_ref("change-state", change_path, change_payload, summary_key="summary", state_key="state"))

    execution_path = _pick_latest_json(workspace / ".forge-artifacts" / "execution-progress")
    execution_payload = _read_json_object(execution_path)
    if execution_path is not None and isinstance(execution_payload, dict):
        latest_execution = execution_payload
        artifacts.append(
            _artifact_ref(
                "execution-progress",
                execution_path,
                execution_payload,
                summary_key="task",
                state_key="completion_state",
            )
        )

    verify_change_root = workspace / ".forge-artifacts" / "verify-change"
    if isinstance(latest_change, dict) and latest_change.get("slug"):
        verify_change_root = verify_change_root / str(latest_change["slug"])
    verify_change_path = _pick_latest_json(verify_change_root)
    verify_change_payload = _read_json_object(verify_change_path)
    if verify_change_path is not None and isinstance(verify_change_payload, dict):
        latest_verify_change = verify_change_payload
        artifacts.append(
            _artifact_ref(
                "verify-change",
                verify_change_path,
                verify_change_payload,
                summary_key="summary",
                state_key="status",
            )
        )

    return artifacts, {
        "latest_execution": latest_execution,
        "latest_change": latest_change,
        "latest_verify_change": latest_verify_change,
    }


def collect_review_artifacts(workspace: Path) -> tuple[list[dict], tuple[str, dict, Path] | None]:
    candidates: list[tuple[str, dict, Path]] = []
    review_state_path = _pick_latest_json(workspace / ".forge-artifacts" / "reviews")
    review_state_payload = _read_json_object(review_state_path)
    if review_state_path is not None and isinstance(review_state_payload, dict):
        candidates.append(("review-state", review_state_payload, review_state_path))

    review_pack_path = _pick_latest_json(workspace / ".forge-artifacts" / "review-packs")
    review_pack_payload = _read_json_object(review_pack_path)
    if review_pack_path is not None and isinstance(review_pack_payload, dict):
        candidates.append(("review-pack", review_pack_payload, review_pack_path))

    refs: list[dict] = []
    for kind, payload, path in candidates:
        if kind == "review-state":
            refs.append(_artifact_ref(kind, path, payload, summary_key="scope", state_key="disposition"))
        else:
            refs.append(_artifact_ref(kind, path, payload, summary_key="summary", state_key="status"))

    if not candidates:
        return refs, None

    latest_kind, latest_payload, latest_path = max(candidates, key=lambda item: _mtime_rank(item[2]))
    return refs, (latest_kind, latest_payload, latest_path)


def validate_supporting_artifacts(args) -> tuple[list[dict], list[dict]]:
    workspace = args.workspace.resolve()
    _validate_required_stage_state(workspace, args.decision)
    process_artifacts, context = collect_process_artifacts(workspace)
    latest_execution = context["latest_execution"]
    latest_change = context["latest_change"]
    latest_verify_change = context["latest_verify_change"]
    if args.target_claim in TARGETS_REQUIRING_PROCESS_ARTIFACT and not process_artifacts:
        raise ValueError(
            f"Quality gate requires an active change or execution-progress artifact before claiming '{args.target_claim}'."
        )

    if (
        args.target_claim in TARGETS_REQUIRING_PROCESS_ARTIFACT
        and isinstance(latest_execution, dict)
        and latest_execution.get("harness_available") == "yes"
        and not latest_execution.get("red_proof")
    ):
        raise ValueError("Harness-backed readiness claims require persisted RED proof in execution-progress.")

    if args.decision == "go" and args.target_claim in TARGETS_REQUIRING_VERIFY_CHANGE and isinstance(latest_change, dict):
        if not isinstance(latest_verify_change, dict):
            raise ValueError(
                f"Go decision for '{args.target_claim}' requires a persisted verify-change artifact for active change work."
            )
        if latest_verify_change.get("status") != "PASS":
            raise ValueError(f"Latest verify-change must be PASS before claiming '{args.target_claim}'.")

    review_artifacts: list[dict] = []
    if args.decision == "go" and args.target_claim in TARGETS_REQUIRING_REVIEW_ARTIFACT:
        review_artifacts, latest_review = collect_review_artifacts(workspace)
        if latest_review is None:
            raise ValueError(
                f"Go decision for '{args.target_claim}' requires a persisted review-state or review-pack artifact."
            )
        latest_kind, latest_payload, _ = latest_review
        if latest_kind == "review-state" and latest_payload.get("disposition") != "ready-for-merge":
            raise ValueError(
                f"Latest review-state must be 'ready-for-merge' before claiming '{args.target_claim}'."
            )
        if latest_kind == "review-pack" and latest_payload.get("status") != "PASS":
            raise ValueError(f"Latest review-pack must be PASS before claiming '{args.target_claim}'.")

    return process_artifacts, review_artifacts
