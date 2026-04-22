from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify
from workflow_state_support import record_workflow_event


STAGES = {
    "frontend": [
        "brief",
        "system-check",
        "implementation",
        "responsive-a11y-review",
        "handover",
    ],
    "visualize": [
        "brief",
        "interaction-model",
        "spec-or-mockup",
        "states-platform-review",
        "handover",
    ],
}


def build_payload(args: argparse.Namespace) -> dict:
    return {
        "project": args.project_name,
        "mode": args.mode,
        "task": args.task,
        "stage": args.stage,
        "status": args.status,
        "notes": args.note,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "remaining_stages": remaining_stages(args.mode, args.stage),
    }


def remaining_stages(mode: str, current_stage: str) -> list[str]:
    stages = STAGES[mode]
    try:
        index = stages.index(current_stage)
    except ValueError:
        return stages
    return stages[index + 1 :]


def persist_payload(payload: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "ui-progress") / payload["mode"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = slugify(payload["task"])[:64] or "ui-task"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_markdown(payload), encoding="utf-8")
    record_workflow_event("ui-progress", payload, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def format_markdown(payload: dict) -> str:
    lines = [
        f"# UI Progress: {payload['task']}",
        "",
        f"- Project: {payload['project']}",
        f"- Mode: {payload['mode']}",
        f"- Current stage: {payload['stage']}",
        f"- Status: {payload['status']}",
        f"- Updated at: {payload['updated_at']}",
        "",
        "## Notes",
    ]
    if payload["notes"]:
        for item in payload["notes"]:
            lines.append(f"- {item}")
    else:
        lines.append("- (none)")

    lines.extend([
        "",
        "## Remaining Stages",
    ])
    if payload["remaining_stages"]:
        for item in payload["remaining_stages"]:
            lines.append(f"- {item}")
    else:
        lines.append("- complete")
    return "\n".join(lines) + "\n"


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Persist lightweight UI progress for frontend or visual-lens work.")
    parser.add_argument("task", help="Task or screen summary")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for workflow-state grouping")
    parser.add_argument("--mode", choices=sorted(STAGES.keys()), required=True, help="frontend or visualize (compatibility mode for the visual lens)")
    parser.add_argument("--stage", required=True, help="Current workflow stage")
    parser.add_argument("--status", choices=["active", "blocked", "done"], default="active", help="Stage status")
    parser.add_argument("--note", action="append", default=[], help="Extra note. Repeatable.")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    payload = build_payload(args)
    print(format_markdown(payload))
    json_path, md_path = persist_payload(payload, args.output_dir)
    print("Persisted UI progress:")
    print(f"- JSON: {json_path}")
    print(f"- Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
