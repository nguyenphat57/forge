from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from prepare_bump_report import build_report, format_text


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


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
