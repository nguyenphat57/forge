from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio
from doctor_companion import collect_companion_checks
from doctor_environment import collect_environment_checks
from doctor_report import build_doctor_report, format_doctor_text, persist_doctor_report
from doctor_runtime import collect_runtime_checks
from doctor_workspace import collect_workspace_checks


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Diagnose Forge workspace, runtime, and environment health.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root to inspect")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on warnings as well as blockers")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    checks = [
        *collect_environment_checks(workspace),
        *collect_workspace_checks(workspace),
        *collect_runtime_checks(),
    ]
    companion_checks, companion_summaries, companion_registry = collect_companion_checks(workspace)
    checks.extend(companion_checks)
    report = build_doctor_report(workspace, checks)
    report["companions"] = companion_summaries
    report["companion_registry"] = companion_registry
    artifact_blocked = any(check["id"] == "artifact-write-access" and check["status"] == "FAIL" for check in checks)
    if not artifact_blocked:
        latest_path = persist_doctor_report(report, args.output_dir or str(workspace))
        report["artifacts"] = {"json": str(latest_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_doctor_text(report))

    if report["status"] == "FAIL":
        return 1
    if args.strict and report["status"] == "WARN":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
