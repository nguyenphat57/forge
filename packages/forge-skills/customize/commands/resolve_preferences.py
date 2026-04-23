from __future__ import annotations

from _forge_customize_command import bootstrap_shared_paths

bootstrap_shared_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio, load_preferences, resolve_response_style


def build_payload(args: argparse.Namespace) -> dict:
    report = load_preferences(
        preferences_file=args.preferences_file,
        workspace=args.workspace,
        strict=args.strict,
        forge_home=args.forge_home,
    )
    warnings = list(report["warnings"])

    return {
        "status": "WARN" if warnings else "PASS",
        "source": report["source"],
        "paths": report.get("paths", {}),
        "allowed_scopes": ["global", "workspace", "both"] if args.workspace is not None else ["global"],
        "preferences": report["preferences"],
        "sources": report.get("sources", {}),
        "output_contract": report["output_contract"],
        "response_style": resolve_response_style(report["preferences"]),
        "warnings": warnings,
    }


def format_text(payload: dict) -> str:
    lines = [
        "Forge Preferences",
        f"- Status: {payload['status']}",
        f"- Source: {payload['source']['type']}",
        f"- File: {payload['source']['path'] or '(defaults)'}",
        "- Preferences:",
    ]
    for key, value in payload["preferences"].items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value
        lines.append(f"  - {key}: {rendered}")
    lines.append("- Sources:")
    for key, value in payload["sources"].items():
        lines.append(f"  - {key}: {value}")
    if payload["output_contract"]:
        lines.append("- Output contract:")
        for line in json.dumps(payload["output_contract"], indent=2, ensure_ascii=False).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("- Output contract: (none)")
    lines.append("- Response style:")
    for key, value in payload["response_style"].items():
        lines.append(f"  - {key}: {value}")
    lines.append(f"- Allowed scopes: {', '.join(payload['allowed_scopes'])}")
    if payload["warnings"]:
        lines.append("- Warnings:")
        for warning in payload["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(
        description="Resolve Forge response-style preferences from adapter-global state or an explicit file."
    )
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root to inspect for .brain/preferences.json")
    parser.add_argument(
        "--forge-home",
        type=Path,
        default=None,
        help="Override adapter state root (defaults to $FORGE_HOME, installed adapter state, bundle-native dev state, or ~/.forge only when no bundle-specific fallback exists)",
    )
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
            print("\n".join(["Forge Preferences", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
