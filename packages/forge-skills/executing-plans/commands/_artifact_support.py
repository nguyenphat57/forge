from __future__ import annotations

import argparse
import json
from pathlib import Path

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

from text_utils import configure_stdio, excerpt_text, repair_text_artifacts, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


FORMAT_CHOICES = ("text", "json")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--input-file", type=Path, help="Optional JSON file used as the base report")
    parser.add_argument("--project", help="Project label for the persisted artifact")
    parser.add_argument("--recorded-at", help="Explicit timestamp for the persisted report")
    parser.add_argument("--output-dir", help="Artifact root override")
    parser.add_argument("--format", choices=FORMAT_CHOICES, default="text", help="Output format")


def clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def clean_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = clean_text(value)
        if item is None or item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned


def add_text(report: dict, key: str, value: object) -> None:
    cleaned = clean_text(value)
    if cleaned is not None:
        report[key] = cleaned


def add_list(report: dict, key: str, values: object) -> None:
    cleaned = clean_list(values)
    if cleaned:
        report[key] = cleaned


def load_input_report(path: Path | None) -> dict:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Input report must be a JSON object: {path}")
    return payload


def finalize_report(base: dict, workspace: Path, *, project: str | None, recorded_at: str | None) -> dict:
    report = dict(base)
    if project:
        report["project"] = project
    elif not clean_text(report.get("project")):
        report["project"] = workspace.name
    if recorded_at:
        report["recorded_at"] = recorded_at
    return repair_text_artifacts(report)


def write_artifact(
    workspace: Path,
    artifact_dir: str,
    stem: str,
    report: dict,
    markdown_lines: list[str],
) -> tuple[Path, Path, Path, Path]:
    artifact_root = workspace / ".forge-artifacts" / artifact_dir / slugify(stem)
    artifact_root.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp_slug()
    json_path = artifact_root / f"{timestamp}.json"
    markdown_path = artifact_root / f"{timestamp}.md"
    latest_json = artifact_root / "latest.json"
    latest_markdown = artifact_root / "latest.md"
    json_text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    markdown_text = "\n".join(markdown_lines).rstrip() + "\n"
    json_path.write_text(json_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    markdown_path.write_text(markdown_text, encoding="utf-8")
    latest_markdown.write_text(markdown_text, encoding="utf-8")
    return json_path, markdown_path, latest_json, latest_markdown


def record_artifact(
    *,
    kind: str,
    artifact_dir: str,
    stem: str,
    report: dict,
    workspace: Path,
    markdown_lines: list[str],
    output_dir: str | None,
) -> dict:
    artifact_path, markdown_path, latest_json, latest_markdown = write_artifact(
        workspace,
        artifact_dir,
        stem,
        report,
        markdown_lines,
    )
    workflow_state_path, events_path = record_workflow_event(
        kind,
        report,
        output_dir=output_dir or str(workspace),
        source_path=artifact_path,
    )
    return {
        "status": "PASS",
        "kind": kind,
        "artifact_path": str(artifact_path),
        "artifact_markdown_path": str(markdown_path),
        "latest_artifact_path": str(latest_json),
        "latest_markdown_path": str(latest_markdown),
        "workflow_state_path": str(workflow_state_path),
        "workflow_events_path": str(events_path),
        "report": report,
    }


def emit_result(result: dict, output_format: str) -> int:
    configure_stdio()
    if output_format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    print(f"[{result['status']}] {result['kind']}: {result['artifact_path']}")
    report = result.get("report", {})
    for key in ("label", "task", "goal", "scope", "target_claim", "summary"):
        value = clean_text(report.get(key))
        if value is not None:
            print(f"{key}: {value}")
            break
    stage = clean_text(report.get("current_stage") or report.get("stage_name") or report.get("stage"))
    if stage is not None:
        print(f"stage: {stage}")
    status = clean_text(report.get("status"))
    if status is not None:
        print(f"status: {status}")
    completion_state = clean_text(report.get("completion_state"))
    if completion_state is not None:
        print(f"completion_state: {completion_state}")
    blockers = clean_list(report.get("blockers"))
    if blockers:
        print(f"blockers: {excerpt_text('; '.join(blockers), max_lines=1, max_chars=220)}")
    print(f"workflow_state: {result['workflow_state_path']}")
    return 0
