from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    configure_stdio,
    extract_extras,
    load_preferences,
    merge_extra_preferences,
    resolve_delegation_preference,
    resolve_output_contract,
    resolve_response_style,
    resolve_workspace_preferences_path,
)


def load_workspace_extra_preferences(
    workspace: Path | None,
    *,
    strict: bool = False,
) -> tuple[dict[str, object], list[str]]:
    if workspace is None:
        return {}, []

    path = resolve_workspace_preferences_path(workspace)
    if not path.exists():
        return {}, []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"Invalid JSON in preferences file: {path}") from exc
        return {}, [f"Invalid JSON in workspace extra preferences file '{path.name}'. Ignoring extras."]

    return extract_extras(payload), []


def build_payload(args: argparse.Namespace) -> dict:
    report = load_preferences(
        preferences_file=args.preferences_file,
        workspace=args.workspace,
        strict=args.strict,
        forge_home=args.forge_home,
    )
    warnings = list(report["warnings"])
    extra = report.get("extra", {})

    if args.workspace is not None and report["source"]["type"] != "workspace-legacy":
        workspace_extra, workspace_warnings = load_workspace_extra_preferences(
            args.workspace,
            strict=args.strict,
        )
        extra = merge_extra_preferences(extra, workspace_extra)
        for warning in workspace_warnings:
            if warning not in warnings:
                warnings.append(warning)

    delegation_preference, delegation_warnings, _ = resolve_delegation_preference(
        extra,
        strict=args.strict,
    )
    extra["delegation_preference"] = delegation_preference
    for warning in delegation_warnings:
        if warning not in warnings:
            warnings.append(warning)

    payload = {
        "status": "WARN" if warnings else "PASS",
        "source": report["source"],
        "preferences": report["preferences"],
        "extra": extra,
        "output_contract": resolve_output_contract(extra),
        "response_style": resolve_response_style(report["preferences"]),
        "warnings": warnings,
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
    if payload["extra"]:
        lines.append("- Extra:")
        for line in json.dumps(payload["extra"], indent=2, ensure_ascii=False).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("- Extra: (none)")
    if payload["output_contract"]:
        lines.append("- Output contract:")
        for line in json.dumps(payload["output_contract"], indent=2, ensure_ascii=False).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("- Output contract: (none)")
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

    parser = argparse.ArgumentParser(
        description="Resolve Forge response-style preferences from adapter-global state or an explicit file."
    )
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root to inspect for legacy .brain/preferences.json")
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
            print("\n".join(["Forge Preferences", f"- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
