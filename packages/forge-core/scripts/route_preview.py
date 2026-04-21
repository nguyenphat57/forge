from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, load_registry
from route_delegation import choose_delegation_plan
from route_preview_builder import build_report as _build_report
from route_preview_output import format_text, persist_report

__all__ = [
    "build_report",
    "choose_delegation_plan",
    "format_text",
    "load_registry",
    "main",
    "persist_report",
]


def build_report(args: argparse.Namespace) -> dict:
    return _build_report(args, load_registry_fn=load_registry)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview Forge routing decisions.")
    parser.add_argument("prompt", help="User prompt or task summary")
    parser.add_argument("--repo-signal", action="append", default=[], help="Repo artifact, path, or signal. Repeatable.")
    parser.add_argument("--workspace-router", type=Path, default=None, help="Optional AGENTS.md or workspace skill map")
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root for preference resolution")
    parser.add_argument("--changed-files", type=int, default=None, help="Optional changed file count to guide complexity")
    parser.add_argument("--recent-small-tasks", type=int, default=None, help="Completed small slices since the last holistic review")
    parser.add_argument(
        "--changed-files-since-review",
        type=int,
        default=None,
        help="Total changed files since the last holistic review",
    )
    parser.add_argument("--has-harness", choices=["auto", "yes", "no"], default="auto", help="Whether a usable test harness is known")
    parser.add_argument(
        "--delegation-preference",
        choices=["off", "auto", "review-lanes", "parallel-workers"],
        default=None,
        help="Optional preview override for resolved delegation preference",
    )
    parser.add_argument("--forge-home", type=Path, default=None, help="Optional Forge state root for preference resolution")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the preview under .forge-artifacts/route-previews")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted route preview:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
