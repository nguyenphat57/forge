from __future__ import annotations

from _forge_core_command import bootstrap_shared_paths

bootstrap_shared_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio
from prepare_bump_report import build_report, format_text


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Prepare or apply a host-neutral version bump checklist.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root containing VERSION and CHANGELOG.md")
    parser.add_argument("--bump", default="auto", help="patch, minor, major, auto, or an explicit semantic version")
    parser.add_argument("--apply", action="store_true", help="Write VERSION and CHANGELOG.md instead of previewing only")
    parser.add_argument("--release-ready", action="store_true", help="Surface the nearest release verification command")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except (FileNotFoundError, ValueError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Bump Preparation", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
