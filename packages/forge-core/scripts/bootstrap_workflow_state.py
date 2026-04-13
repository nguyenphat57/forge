from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio
from workflow_state_bootstrap_support import seed_workflow_state_from_sidecars
from workflow_state_support import record_workflow_event, resolve_workflow_state


def build_report(workspace: Path, project_name: str) -> dict:
    warnings: list[str] = []
    existing = resolve_workflow_state(workspace, warnings, auto_seed_missing=False)
    if isinstance(existing.get("state"), dict):
        return {
            "status": "PASS",
            "workspace": str(workspace),
            "project": project_name,
            "bootstrap_source": "workflow-state",
            "latest_path": existing.get("path"),
            "warnings": warnings,
        }

    seeded = seed_workflow_state_from_sidecars(
        workspace,
        warnings,
        project_name=project_name,
        record_event=record_workflow_event,
    )
    if seeded is not None:
        return {
            "status": "PASS",
            "workspace": str(workspace),
            "project": project_name,
            "bootstrap_source": seeded["bootstrap_source"],
            "latest_path": seeded["latest_path"],
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
