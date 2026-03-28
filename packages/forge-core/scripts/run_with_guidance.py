from __future__ import annotations

import argparse
import json
import shlex
from datetime import datetime, timezone
from pathlib import Path

from common import (
    configure_stdio,
    default_artifact_dir,
    excerpt_text,
    load_preferences,
    resolve_response_style,
    slugify,
    timestamp_slug,
    translate_error_text,
)
from run_guidance_support import (
    build_evidence,
    classify_command_kind,
    determine_guidance,
    execute_command,
)
from workflow_state_support import record_workflow_event


def normalize_command(command: list[str]) -> list[str]:
    normalized = command[:]
    if normalized and normalized[0] == "--":
        normalized = normalized[1:]
    return normalized


def quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def build_report(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    if not workspace.exists() or not workspace.is_dir():
        raise FileNotFoundError(f"Workspace does not exist: {workspace}")

    command = normalize_command(args.command)
    if not command:
        raise ValueError("Missing command. Pass the command after `--`.")

    preferences_report = load_preferences(workspace=workspace)
    response_style = resolve_response_style(preferences_report["preferences"])
    execution = execute_command(command, workspace, args.timeout_ms)
    combined_output = "\n".join(part for part in (execution["stdout"], execution["stderr"]) if part).strip()
    readiness_detected = execution["readiness_detected"]
    command_kind = classify_command_kind(command, combined_output, readiness_detected)
    state, suggested_workflow, recommended_action = determine_guidance(
        command_kind,
        execution,
        readiness_detected,
    )
    status = "PASS" if state in {"completed", "running"} else "FAIL"
    warnings = preferences_report["warnings"][:]
    error_translation = None

    if execution["timed_out"] and readiness_detected:
        warnings.append("Command exceeded timeout after a ready signal; treat the process as still running.")
    elif execution["timed_out"]:
        warnings.append("Command exceeded timeout before a ready signal was detected.")
        error_translation = translate_error_text("timed out", include_empty_fallback=True)
    elif execution["exit_code"] != 0:
        error_translation = translate_error_text(combined_output, include_empty_fallback=True)

    if error_translation is not None and state in {"failed", "timed-out"}:
        recommended_action = error_translation["suggested_action"]

    command_display = quote_command(command)
    return {
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": args.project_name,
        "workspace": str(workspace),
        "command": command,
        "command_display": command_display,
        "command_kind": command_kind,
        "state": state,
        "exit_code": execution["exit_code"],
        "timed_out": execution["timed_out"],
        "duration_ms": execution["duration_ms"],
        "readiness_detected": readiness_detected,
        "suggested_workflow": suggested_workflow,
        "recommended_action": recommended_action,
        "stdout_excerpt": excerpt_text(execution["stdout"]),
        "stderr_excerpt": excerpt_text(execution["stderr"]),
        "error_translation": error_translation,
        "evidence": build_evidence(command_display, execution, workspace),
        "response_style": response_style,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Run Guidance",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Command: {report['command_display']}",
        f"- State: {report['state']}",
        f"- Kind: {report['command_kind']}",
        f"- Suggested workflow: {report['suggested_workflow']}",
        f"- Recommended action: {report['recommended_action']}",
        f"- Readiness detected: {'yes' if report['readiness_detected'] else 'no'}",
        f"- Exit code: {report['exit_code'] if report['exit_code'] is not None else '(none)'}",
        f"- Duration ms: {report['duration_ms']}",
    ]
    if report["stdout_excerpt"]:
        lines.append("- Stdout excerpt:")
        for line in report["stdout_excerpt"].splitlines():
            lines.append(f"  {line}")
    if report["stderr_excerpt"]:
        lines.append("- Stderr excerpt:")
        for line in report["stderr_excerpt"].splitlines():
            lines.append(f"  {line}")
    if report["error_translation"] is not None:
        lines.append("- Error translation:")
        lines.append(f"  - Meaning: {report['error_translation']['human_message']}")
        lines.append(f"  - Suggested action: {report['error_translation']['suggested_action']}")
        if report["error_translation"]["error_excerpt"]:
            lines.append(f"  - Snippet: {report['error_translation']['error_excerpt']}")
    lines.append("- Evidence:")
    for item in report["evidence"]:
        lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    artifacts = report.get("artifacts")
    if artifacts:
        lines.append("- Artifacts:")
        lines.append(f"  - JSON: {artifacts['json']}")
        lines.append(f"  - Markdown: {artifacts['markdown']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "run-reports")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(Path(report['workspace']).name)}-{report['command_kind']}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    record_workflow_event("run-report", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run a command and return host-neutral Forge guidance for what to do next.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root where the command should run")
    parser.add_argument("--timeout-ms", type=int, default=20000, help="Timeout budget for the command")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for workflow-state grouping")
    parser.add_argument("--persist", action="store_true", help="Persist the report under .forge-artifacts/run-reports")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run, passed after `--`")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except (FileNotFoundError, ValueError, OSError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Run Guidance", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
