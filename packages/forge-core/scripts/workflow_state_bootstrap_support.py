from __future__ import annotations

import json
from pathlib import Path

from workflow_state_io import now_iso, pick_latest_json, read_json_object


LEGACY_BOOTSTRAP_SOURCES = (
    ("route-preview", ".forge-artifacts/route-previews", "route preview"),
    ("direction-state", ".forge-artifacts/direction", "direction state"),
    ("legacy-spec-review-state", ".forge-artifacts/spec-review", "legacy spec review state"),
    ("execution-progress", ".forge-artifacts/execution-progress", "execution progress"),
    ("review-state", ".forge-artifacts/reviews", "review state"),
    ("quality-gate", ".forge-artifacts/quality-gates", "quality gate"),
)


def _extract_markdown_title(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if ":" in title and title.split(":", 1)[0].lower() in {"plan", "spec"}:
                return title.split(":", 1)[1].strip()
            return title
    return path.stem


def _find_latest_markdown(workspace: Path, relative_dir: str) -> Path | None:
    base_dir = workspace / relative_dir
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob("*.md"):
        try:
            rank = candidate.stat().st_mtime, str(candidate).lower()
        except OSError:
            rank = (float("-inf"), "")
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def _best_effort_project_name(workspace: Path) -> str:
    for candidate in (workspace / "README.md", workspace / "README"):
        title = _extract_markdown_title(candidate)
        if title:
            return title
    package_json = workspace / "package.json"
    if package_json.exists():
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            name = payload.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    return workspace.name


def _persist_bootstrap_stage(
    workspace: Path,
    project_name: str,
    source_path: Path,
    *,
    stage_name: str,
    activation_reason: str,
    record_event,
) -> Path:
    report = {
        "project": project_name,
        "workspace": str(workspace),
        "recorded_at": now_iso(),
        "stage_name": stage_name,
        "stage_status": "active",
        "current_stage": stage_name,
        "required_stage_chain": [stage_name],
        "activation_reason": activation_reason,
        "artifact_refs": [str(source_path)],
        "evidence_refs": [],
        "summary": _extract_markdown_title(source_path) or source_path.stem,
        "notes": [],
        "next_actions": [],
    }
    latest_path, _ = record_event("stage-state", report, output_dir=str(workspace), source_path=source_path)
    return latest_path


def seed_workflow_state_from_sidecars(
    workspace: Path,
    warnings: list[str] | None = None,
    *,
    project_name: str | None = None,
    record_event,
) -> dict | None:
    local_warnings = warnings if warnings is not None else []
    for kind, relative_dir, label in LEGACY_BOOTSTRAP_SOURCES:
        source_path = pick_latest_json(workspace / Path(relative_dir))
        payload = read_json_object(source_path, label, local_warnings) if source_path is not None else None
        if isinstance(payload, dict):
            latest_path, _ = record_event(kind, payload, output_dir=str(workspace), source_path=source_path)
            return {"bootstrap_source": kind, "latest_path": str(latest_path)}

    inferred_project = project_name or _best_effort_project_name(workspace)
    latest_plan = _find_latest_markdown(workspace, "docs/plans")
    if latest_plan is not None:
        latest_path = _persist_bootstrap_stage(
            workspace,
            inferred_project,
            latest_plan,
            stage_name="plan",
            activation_reason="Bootstrapped from latest plan document.",
            record_event=record_event,
        )
        return {"bootstrap_source": "plan", "latest_path": str(latest_path)}

    latest_spec = _find_latest_markdown(workspace, "docs/specs")
    if latest_spec is not None:
        latest_path = _persist_bootstrap_stage(
            workspace,
            inferred_project,
            latest_spec,
            stage_name="architect",
            activation_reason="Bootstrapped from latest spec document.",
            record_event=record_event,
        )
        return {"bootstrap_source": "spec", "latest_path": str(latest_path)}

    return None
