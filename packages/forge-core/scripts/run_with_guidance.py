from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import time
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


READINESS_PATTERNS = (
    re.compile(r"\bready\b", re.IGNORECASE),
    re.compile(r"\blistening on\b", re.IGNORECASE),
    re.compile(r"\brunning on\b", re.IGNORECASE),
    re.compile(r"\bserver started\b", re.IGNORECASE),
    re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)[:/\w.-]*", re.IGNORECASE),
)

BUILD_HINTS = (
    "build",
    "compile",
    "bundle",
    "assemble",
    "pack",
    "tsc",
)

SERVE_HINTS = (
    "serve",
    "start",
    "dev",
    "preview",
    "watch",
    "localhost",
    "0.0.0.0",
)

DEPLOY_HINTS = (
    "deploy",
    "release",
    "publish",
    "ship",
    "wrangler",
    "vercel",
    "netlify",
    "flyctl",
)


def normalize_command(command: list[str]) -> list[str]:
    normalized = command[:]
    if normalized and normalized[0] == "--":
        normalized = normalized[1:]
    return normalized


def quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)

def detect_readiness(output: str) -> bool:
    if not output.strip():
        return False
    return any(pattern.search(output) for pattern in READINESS_PATTERNS)


def hint_in_text(text: str, hint: str) -> bool:
    pattern = r"(?<![a-z0-9]){0}(?![a-z0-9])".format(re.escape(hint))
    return re.search(pattern, text, re.IGNORECASE) is not None


def classify_command_kind(command: list[str], combined_output: str, readiness_detected: bool) -> str:
    haystack = " ".join(part.casefold() for part in command)
    output = combined_output.casefold()
    if any(hint_in_text(haystack, hint) or hint_in_text(output, hint) for hint in DEPLOY_HINTS):
        return "deploy"
    if readiness_detected or any(hint_in_text(haystack, hint) for hint in SERVE_HINTS):
        return "serve"
    if any(hint_in_text(haystack, hint) or hint_in_text(output, hint) for hint in BUILD_HINTS) or "build completed successfully" in output:
        return "build"
    return "generic"


def execute_command(command: list[str], workspace: Path, timeout_ms: int) -> dict:
    start = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_ms / 1000)
        exit_code = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        process.kill()
        tail_stdout, tail_stderr = process.communicate()
        stdout += tail_stdout or ""
        stderr += tail_stderr or ""
        exit_code = None

    duration_ms = int((time.perf_counter() - start) * 1000)
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
    }


def determine_guidance(command_kind: str, execution: dict, readiness_detected: bool) -> tuple[str, str, str]:
    if execution["timed_out"] and readiness_detected:
        return (
            "running",
            "test",
            "Service looks ready. Run a targeted smoke or API check while the process is healthy.",
        )

    if execution["timed_out"]:
        return (
            "timed-out",
            "debug",
            "Command timed out without a clear ready signal. Inspect the last output and debug the stall before retrying.",
        )

    if execution["exit_code"] != 0:
        return (
            "failed",
            "debug",
            "Use the failing command as the reproduction anchor, then debug the root cause before trying a broader fix.",
        )

    if command_kind == "deploy":
        return (
            "completed",
            "deploy",
            "Run post-deploy verification and confirm rollback readiness before calling the release complete.",
        )

    if command_kind == "serve":
        return (
            "completed",
            "test",
            "Service started cleanly. Run the nearest smoke or manual verification against the live entrypoint.",
        )

    if command_kind == "build":
        return (
            "completed",
            "test",
            "Build passed. Run the nearest targeted test or smoke check before claiming the slice is done.",
        )

    return (
        "completed",
        "test",
        "Command completed. Validate the outcome with the nearest targeted verification before moving on.",
    )


def build_evidence(command_display: str, execution: dict, workspace: Path) -> list[str]:
    evidence = [
        f"workspace: {workspace}",
        f"command: {command_display}",
        f"duration_ms: {execution['duration_ms']}",
    ]
    if execution["stdout"].strip():
        evidence.append(f"stdout: {excerpt_text(execution['stdout'])}")
    if execution["stderr"].strip():
        evidence.append(f"stderr: {excerpt_text(execution['stderr'])}")
    if execution["timed_out"]:
        evidence.append("timeout: command exceeded the requested timeout budget")
    return evidence


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
    readiness_detected = detect_readiness(combined_output)
    command_kind = classify_command_kind(command, combined_output, readiness_detected)
    state, suggested_workflow, recommended_action = determine_guidance(command_kind, execution, readiness_detected)
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
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run a command and return host-neutral Forge guidance for what to do next.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root where the command should run")
    parser.add_argument("--timeout-ms", type=int, default=20000, help="Timeout budget for the command")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
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
