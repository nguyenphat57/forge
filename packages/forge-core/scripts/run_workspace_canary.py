from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio
from run_workspace_canary_core import (
    MARKER_DIRS,
    MARKER_FILES,
    build_report,
    build_route_args,
    collect_repo_signals,
    default_scenarios,
    evaluate_route_scenario,
    run_router_check,
)
from run_workspace_canary_persist import format_text, persist_canary_result, persist_report


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run an automated Forge canary pack against a real workspace.")
    parser.add_argument("workspace", type=Path, help="Workspace root to evaluate")
    parser.add_argument("--workspace-name", default=None, help="Optional label for artifacts and summaries")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist workspace canary and canary-run artifacts")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve(), args.workspace_name)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        detail_json, detail_md = persist_report(report, args.output_dir)
        canary_json, canary_md = persist_canary_result(report, args.output_dir)
        print("\nPersisted workspace canary:")
        print(f"- Detail JSON: {detail_json}")
        print(f"- Detail Markdown: {detail_md}")
        print(f"- Canary JSON: {canary_json}")
        print(f"- Canary Markdown: {canary_md}")

    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
