from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, write_preferences


def build_report(args: argparse.Namespace) -> dict:
    updates: dict[str, str] = {}
    extra_updates: dict[str, object] = {}
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
    for field in ("language", "orthography", "delegation_preference"):
        value = getattr(args, field)
        if value is not None:
            extra_updates[field] = value
    for field in ("language", "orthography", "delegation_preference"):
        if getattr(args, f"clear_{field}"):
            extra_updates[field] = None

    return write_preferences(
        workspace=args.workspace,
        updates=updates,
        extra_updates=extra_updates,
        strict=args.strict,
        replace=args.replace,
        apply=args.apply,
        forge_home=args.forge_home,
    )


def format_text(report: dict) -> str:
    lines = [
        "Forge Preferences Update",
        f"- Status: {report['status']}",
        f"- Scope: {report['scope']}",
        f"- State root: {report['state_root']}",
        f"- File: {report['path']}",
        f"- Extra file: {report['extra_path']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        f"- Replace mode: {'yes' if report['replace'] else 'no'}",
        "- Changed fields:",
    ]
    if report["workspace"]:
        lines.insert(4, f"- Workspace fallback: {report['workspace']}")
    if report["changed_fields"]:
        for field in report["changed_fields"]:
            lines.append(f"  - {field}")
    else:
        lines.append("  - (none)")

    lines.append("- Changed extra fields:")
    if report["changed_extra_fields"]:
        for field in report["changed_extra_fields"]:
            lines.append(f"  - {field}")
    else:
        lines.append("  - (none)")

    lines.append("- Preferences:")
    for key, value in report["preferences"].items():
        lines.append(f"  - {key}: {value}")

    if report["extra"]:
        lines.append("- Extra:")
        for line in json.dumps(report["extra"], indent=2, ensure_ascii=False).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("- Extra: (none)")

    if report["output_contract"]:
        lines.append("- Output contract:")
        for line in json.dumps(report["output_contract"], indent=2, ensure_ascii=False).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("- Output contract: (none)")

    lines.append("- Response style:")
    for key, value in report["response_style"].items():
        lines.append(f"  - {key}: {value}")

    if report["warnings"]:
        lines.append("- Warnings:")
        for warning in report["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: (none)")
    if report["migrated_legacy_workspace_preferences"]:
        lines.append("- Migration: reused legacy workspace preferences as the base before writing adapter-global state")
    if report.get("migrated_legacy_global_preferences"):
        lines.append("- Migration: converted legacy adapter-global single-file state into split canonical + extra files")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(
        description="Preview or write host-neutral Forge preferences in the adapter-global state file."
    )
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root to inspect for legacy .brain/preferences.json during migration")
    parser.add_argument(
        "--forge-home",
        type=Path,
        default=None,
        help="Override adapter state root (defaults to $FORGE_HOME, installed adapter state, bundle-native dev state, or ~/.forge only when no bundle-specific fallback exists)",
    )
    parser.add_argument("--technical-level", dest="technical_level", help="technical_level value or alias")
    parser.add_argument("--detail-level", dest="detail_level", help="detail_level value or alias")
    parser.add_argument("--autonomy-level", dest="autonomy_level", help="autonomy_level value or alias")
    parser.add_argument("--pace", help="pace value or alias")
    parser.add_argument("--feedback-style", dest="feedback_style", help="feedback_style value or alias")
    parser.add_argument("--personality", help="personality value or alias")
    parser.add_argument("--language", help="Optional host-native output language hint to persist alongside canonical preferences")
    parser.add_argument("--orthography", help="Optional host-native orthography hint to persist alongside canonical preferences")
    parser.add_argument(
        "--delegation-preference",
        dest="delegation_preference",
        help="Optional typed delegation preference: off, auto, review-lanes, or parallel-workers",
    )
    parser.add_argument("--clear-language", action="store_true", help="Remove any persisted host-native language hint")
    parser.add_argument("--clear-orthography", action="store_true", help="Remove any persisted host-native orthography hint")
    parser.add_argument("--clear-delegation-preference", action="store_true", help="Remove any persisted delegation preference override")
    parser.add_argument("--replace", action="store_true", help="Start from schema defaults instead of merging with current preferences")
    parser.add_argument("--apply", action="store_true", help="Write the adapter-global Forge preferences file instead of preview only")
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
