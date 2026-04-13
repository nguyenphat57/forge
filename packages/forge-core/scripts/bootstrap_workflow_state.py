from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, slugify
from help_next_support import extract_markdown_title, find_latest_markdown
from record_stage_state import persist_stage_report
from workflow_state_io import pick_latest_json, read_json_object
from workflow_state_support import record_workflow_event, resolve_workflow_state


LEGACY_JSON_SOURCES = (
    ("route-preview", ".forge-artifacts/route-previews", "route preview"),
    ("direction-state", ".forge-artifacts/direction", "direction state"),
    ("spec-review-state", ".forge-artifacts/spec-review", "spec review state"),
    ("execution-progress", ".forge-artifacts/execution-progress", "execution progress"),
    ("review-state", ".forge-artifacts/reviews", "review state"),
    ("quality-gate", ".forge-artifacts/quality-gates", "quality gate"),
)


def _persist_plan_stage(workspace: Path, project_name: str, plan_path: Path) -> Path:
    report = {
        "project": project_name,
        "workspace": str(workspace),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage_name": "plan",
        "stage_status": "active",
        "current_stage": "plan",
        "required_stage_chain": ["plan"],
        "activation_reason": "Bootstrapped from latest plan document.",
        "artifact_refs": [str(plan_path)],
        "evidence_refs": [],
        "summary": extract_markdown_title(plan_path) or plan_path.stem,
        "notes": [],
        "next_actions": [],
    }
    # Reuse the generic recorder so the bootstrap path exercises the canonical write surface.
    persist_stage_report(report, str(workspace))
    return workspace / ".forge-artifacts" / "workflow-state" / slugify(project_name) / "latest.json"


def _persist_spec_stage(workspace: Path, project_name: str, spec_path: Path) -> Path:
    report = {
        "project": project_name,
        "workspace": str(workspace),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage_name": "architect",
        "stage_status": "active",
        "current_stage": "architect",
        "required_stage_chain": ["architect"],
        "activation_reason": "Bootstrapped from latest spec document.",
        "artifact_refs": [str(spec_path)],
        "evidence_refs": [],
        "summary": extract_markdown_title(spec_path) or spec_path.stem,
        "notes": [],
        "next_actions": [],
    }
    persist_stage_report(report, str(workspace))
    return workspace / ".forge-artifacts" / "workflow-state" / slugify(project_name) / "latest.json"


def build_report(workspace: Path, project_name: str) -> dict:
    warnings: list[str] = []
    existing = resolve_workflow_state(workspace, warnings)
    if isinstance(existing.get("state"), dict):
        return {
            "status": "PASS",
            "workspace": str(workspace),
            "project": project_name,
            "bootstrap_source": "workflow-state",
            "latest_path": existing.get("path"),
            "warnings": warnings,
        }

    for kind, relative_dir, label in LEGACY_JSON_SOURCES:
        source_path = pick_latest_json(workspace / Path(relative_dir))
        payload = read_json_object(source_path, label, warnings) if source_path is not None else None
        if isinstance(payload, dict):
            latest_path, _ = record_workflow_event(kind, payload, output_dir=str(workspace), source_path=source_path)
            return {
                "status": "PASS",
                "workspace": str(workspace),
                "project": project_name,
                "bootstrap_source": kind,
                "latest_path": str(latest_path),
                "warnings": warnings,
            }

    latest_plan = find_latest_markdown(workspace, "docs/plans")
    if latest_plan is not None:
        latest_path = _persist_plan_stage(workspace, project_name, latest_plan)
        return {
            "status": "PASS",
            "workspace": str(workspace),
            "project": project_name,
            "bootstrap_source": "plan",
            "latest_path": str(latest_path),
            "warnings": warnings,
        }

    latest_spec = find_latest_markdown(workspace, "docs/specs")
    if latest_spec is not None:
        latest_path = _persist_spec_stage(workspace, project_name, latest_spec)
        return {
            "status": "PASS",
            "workspace": str(workspace),
            "project": project_name,
            "bootstrap_source": "spec",
            "latest_path": str(latest_path),
            "warnings": warnings,
        }

    warnings.append("No legacy workflow artifact or plan/spec sidecar was available to seed canonical workflow-state.")
    return {
        "status": "WARN",
        "workspace": str(workspace),
        "project": project_name,
        "bootstrap_source": None,
        "latest_path": None,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Workflow Bootstrap",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Project: {report['project']}",
        f"- Bootstrap source: {report['bootstrap_source'] or '(none)'}",
        f"- Latest path: {report['latest_path'] or '(none)'}",
    ]
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Seed canonical workflow-state from one legacy source.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--project-name", default="", help="Project or workspace name")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    project_name = args.project_name or workspace.name
    report = build_report(workspace, project_name)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
