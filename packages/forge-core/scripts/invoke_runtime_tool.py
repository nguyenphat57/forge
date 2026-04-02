from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from runtime_tool_support import (
    available_runtime_tool_names,
    resolve_runtime_tool,
    runtime_error_taxonomy,
    runtime_health_report,
)
from workflow_state_support import record_workflow_event


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Invoke a registered Forge runtime tool through the current bundle.",
        epilog="Wrapper options must appear before the runtime bundle name; everything after the bundle is forwarded.",
    )
    parser.add_argument("--tool-target", help="Override runtime tool root path")
    parser.add_argument("--workspace", type=Path, default=None, help="Workspace for optional workflow-state recording")
    parser.add_argument("--project-name", default="workspace", help="Project name for workflow-state recording")
    parser.add_argument("--packet-id", default=None, help="Packet identifier when recording browser proof")
    parser.add_argument("--current-stage", default=None, help="Current stage when recording browser proof")
    parser.add_argument("--record-browser-proof", action="store_true", help="Record browser proof into workflow-state")
    parser.add_argument("--browser-proof-target", default=None, help="Optional human label for the browser proof target")
    parser.add_argument("--doctor", action="store_true", help="Run runtime health diagnostics and exit")
    parser.add_argument("bundle", choices=available_runtime_tool_names(), help="Runtime tool bundle name")
    parser.add_argument("tool_args", nargs=argparse.REMAINDER, help="Arguments forwarded to the runtime tool")
    args = parser.parse_args()
    tool_args = list(args.tool_args)

    if tool_args[:1] == ["--"]:
        tool_args = tool_args[1:]

    health = runtime_health_report(args.bundle, explicit_target=args.tool_target)
    if args.doctor:
        print(json.dumps(health, indent=2, ensure_ascii=False))
        return 0 if health["status"] in {"PASS", "WARN"} else 1

    if health["status"] == "FAIL":
        print(json.dumps(health, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    payload = resolve_runtime_tool(args.bundle, explicit_target=args.tool_target)
    if payload["status"] != "PASS":
        failure = dict(payload)
        failure["runtime_health"] = health
        print(json.dumps(failure, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    completed = subprocess.run(
        [sys.executable, str(payload["script_path"]), *tool_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)

    parsed_output: dict | None = None
    if completed.stdout.strip():
        try:
            candidate = json.loads(completed.stdout)
        except json.JSONDecodeError:
            candidate = None
        if isinstance(candidate, dict):
            parsed_output = candidate

    if args.record_browser_proof and args.workspace is not None:
        runtime_failure = (
            runtime_error_taxonomy("tool-failed", completed.stderr)
            if completed.returncode != 0
            else None
        )
        health_note = (
            f" Runtime health warning: {health.get('summary')}"
            if health.get("status") == "WARN"
            else ""
        )
        proof_result = (
            parsed_output.get("status")
            if isinstance(parsed_output, dict) and isinstance(parsed_output.get("status"), str)
            else "PASS"
            if completed.returncode == 0
            else "FAIL"
        )
        run_report = {
            "status": "PASS" if completed.returncode == 0 else "FAIL",
            "project": args.project_name,
            "command_display": " ".join([args.bundle, *tool_args]).strip(),
            "command_kind": "browser-qa",
            "state": "completed" if completed.returncode == 0 else "failed",
            "suggested_workflow": "review" if completed.returncode == 0 else "debug",
            "recommended_action": (
                f"Browser proof recorded for packet '{args.packet_id}'."
                if completed.returncode == 0 and isinstance(args.packet_id, str) and args.packet_id
                else "Browser proof recorded."
                if completed.returncode == 0
                else "Browser proof failed. Debug the browser path before continuing."
            )
            + health_note,
            "warnings": [],
            "current_stage": args.current_stage,
            "packet_id": args.packet_id,
            "browser_proof_status": "satisfied" if completed.returncode == 0 else "blocked",
            "browser_proof_result": proof_result,
            "browser_proof_target": args.browser_proof_target or (tool_args[0] if tool_args else args.bundle),
            "runtime_health_status": health.get("status"),
            "runtime_health_taxonomy": health.get("taxonomy"),
            "runtime_health_summary": health.get("summary"),
            "runtime_resolution_source": payload.get("resolution_source"),
            "runtime_registry_path": health.get("registry_path"),
            "runtime_failure_taxonomy": runtime_failure,
            "runtime_doctor_command": f"python scripts/invoke_runtime_tool.py --doctor {args.bundle}",
        }
        record_workflow_event("run-report", run_report, output_dir=str(args.workspace))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
