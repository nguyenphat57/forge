from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, write_preferences


def build_report(args: argparse.Namespace) -> dict:
    updates: dict[str, str] = {}
    for field in (
        "technical_level",
        "detail_level",
        "autonomy_level",
        "pace",
        "feedback_style",
        "personality",
    ):
        value = getattr(args, field)
        if value is not None:
            updates[field] = value

    return write_preferences(
        workspace=args.workspace,
        updates=updates,
        strict=args.strict,
        replace=args.replace,
        apply=args.apply,
    )


def format_text(report: dict) -> str:
    lines = [
        "Forge Preferences Update",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- File: {report['path']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        f"- Replace mode: {'yes' if report['replace'] else 'no'}",
        "- Changed fields:",
    ]
    if report["changed_fields"]:
        for field in report["changed_fields"]:
            lines.append(f"  - {field}")
    else:
        lines.append("  - (none)")

    lines.append("- Preferences:")
    for key, value in report["preferences"].items():
        lines.append(f"  - {key}: {value}")

    lines.append("- Response style:")
    for key, value in report["response_style"].items():
        lines.append(f"  - {key}: {value}")

    if report["warnings"]:
        lines.append("- Warnings:")
        for warning in report["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview or write host-neutral Forge preferences for a workspace.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--technical-level", dest="technical_level", help="technical_level value or alias")
    parser.add_argument("--detail-level", dest="detail_level", help="detail_level value or alias")
    parser.add_argument("--autonomy-level", dest="autonomy_level", help="autonomy_level value or alias")
    parser.add_argument("--pace", help="pace value or alias")
    parser.add_argument("--feedback-style", dest="feedback_style", help="feedback_style value or alias")
    parser.add_argument("--personality", help="personality value or alias")
    parser.add_argument("--replace", action="store_true", help="Start from schema defaults instead of merging with current preferences")
    parser.add_argument("--apply", action="store_true", help="Write `.brain/preferences.json` instead of preview only")
    parser.add_argument("--strict", action="store_true", help="Fail on invalid values instead of warning and falling back")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except (FileNotFoundError, ValueError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Preferences Update", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
