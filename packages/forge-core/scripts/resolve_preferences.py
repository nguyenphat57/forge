from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, load_preferences, resolve_response_style


def build_payload(args: argparse.Namespace) -> dict:
    report = load_preferences(
        preferences_file=args.preferences_file,
        workspace=args.workspace,
        strict=args.strict,
    )
    payload = {
        "status": "WARN" if report["warnings"] else "PASS",
        "source": report["source"],
        "preferences": report["preferences"],
        "response_style": resolve_response_style(report["preferences"]),
        "warnings": report["warnings"],
    }
    return payload


def format_text(payload: dict) -> str:
    lines = [
        "Forge Preferences",
        f"- Status: {payload['status']}",
        f"- Source: {payload['source']['type']}",
        f"- File: {payload['source']['path'] or '(defaults)'}",
        "- Preferences:",
    ]
    for key, value in payload["preferences"].items():
        lines.append(f"  - {key}: {value}")
    lines.append("- Response style:")
    for key, value in payload["response_style"].items():
        lines.append(f"  - {key}: {value}")
    if payload["warnings"]:
        lines.append("- Warnings:")
        for warning in payload["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Resolve Forge response-style preferences from a workspace or explicit file.")
    parser.add_argument("--workspace", type=Path, default=None, help="Workspace root to inspect for .brain/preferences.json")
    parser.add_argument("--preferences-file", type=Path, default=None, help="Explicit preferences file to read")
    parser.add_argument("--strict", action="store_true", help="Fail on invalid values instead of warning and falling back")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        payload = build_payload(args)
    except (FileNotFoundError, ValueError) as exc:
        if args.format == "json":
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Preferences", f"- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
