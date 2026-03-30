from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio
from verify_change_support import evaluate_change, format_report, persist_report


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Verify a Forge change against its durable artifacts.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--slug", default=None, help="Active change slug. Defaults to the latest active change.")
    parser.add_argument("--persist", action="store_true", help="Persist the verify-change artifact")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = evaluate_change(args.workspace.resolve(), args.slug)
    except FileNotFoundError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Verify Change", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir or str(args.workspace.resolve()))
        report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report(report))
    return 0 if report["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
