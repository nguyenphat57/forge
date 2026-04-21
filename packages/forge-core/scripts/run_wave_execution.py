from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio
from wave_execution import advance_wave_execution, plan_wave_execution
from wave_execution_state import (
    build_wave_chain_report,
    load_latest_execution_progress,
    load_latest_run_reports,
    load_packet_file,
    load_wave_plan,
    persist_wave_plan_and_state,
)


def _format_text(plan: dict) -> str:
    current_wave = plan.get("current_wave")
    current_wave_label = f"wave-{current_wave + 1}" if isinstance(current_wave, int) else "(complete)"
    lines = [
        "Forge Wave Execution",
        f"- Wave plan: {plan.get('wave_plan_id', '(none)')}",
        f"- Status: {plan.get('status', '(unknown)')}",
        f"- Current wave: {current_wave_label}",
        f"- Ready packets: {', '.join(plan.get('ready_packets', [])) or '(none)'}",
        f"- Running packets: {', '.join(plan.get('running_packets', [])) or '(none)'}",
        f"- Completed packets: {', '.join(plan.get('completed_packets', [])) or '(none)'}",
        f"- Blocked packets: {', '.join(plan.get('blocked_packets', [])) or '(none)'}",
        f"- Next merge point: {plan.get('next_merge_point') or '(none)'}",
    ]
    return "\n".join(lines)


def _emit(plan: dict, *, format_name: str) -> None:
    if format_name == "json":
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return
    print(_format_text(plan))


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Plan and advance Forge wave execution for packetized work.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command_name in ("plan", "advance", "status"):
        command = subparsers.add_parser(command_name)
        command.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
        command.add_argument("--project-name", required=True, help="Project or workspace name")
        command.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
        if command_name == "plan":
            command.add_argument("--packet-file", type=Path, required=True, help="JSON packet file")

    args = parser.parse_args()
    workspace = args.workspace.resolve()

    try:
        if args.command == "plan":
            packets = load_packet_file(args.packet_file.resolve())
            plan = plan_wave_execution(packets, project=args.project_name)
        else:
            plan = load_wave_plan(workspace, args.project_name)
            latest_progress = load_latest_execution_progress(workspace, args.project_name)
            latest_run_reports = load_latest_run_reports(workspace, args.project_name)
            plan = advance_wave_execution(plan, latest_progress, latest_run_reports)
        persist_wave_plan_and_state(plan, workspace, args.project_name)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"Forge Wave Execution\n- Status: FAIL\n- Error: {exc}")
        return 1

    _emit(plan, format_name=args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
