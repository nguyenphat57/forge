from __future__ import annotations

from _forge_customize_command import bootstrap_shared_paths

bootstrap_shared_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio, write_preferences


CANONICAL_FIELDS = (
    "technical_level",
    "detail_level",
    "autonomy_level",
    "pace",
    "feedback_style",
    "personality",
    "language",
    "orthography",
    "tone_detail",
    "output_quality",
    "custom_rules",
)


def _collect_updates(args: argparse.Namespace) -> tuple[dict[str, object], set[str]]:
    updates: dict[str, object] = {}
    clear_fields: set[str] = set(getattr(args, "clear_field", []) or [])

    for field in CANONICAL_FIELDS:
        value = getattr(args, field)
        if value is not None:
            updates[field] = value

    if args.clear_language:
        clear_fields.add("language")
    if args.clear_orthography:
        clear_fields.add("orthography")
    return updates, clear_fields


def build_report(args: argparse.Namespace) -> dict:
    updates, clear_fields = _collect_updates(args)
    return write_preferences(
        workspace=args.workspace,
        updates=updates,
        clear_fields=clear_fields,
        strict=args.strict,
        replace=args.replace,
        apply=args.apply,
        forge_home=args.forge_home,
        scope=args.scope,
    )


def format_text(report: dict) -> str:
    lines = [
        "Forge Preferences Update",
        f"- Status: {report['status']}",
        f"- Scope: {report['scope']}",
        f"- State root: {report['state_root']}",
        f"- Targets: {', '.join(report['targets']) or '(none)'}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        f"- Replace mode: {'yes' if report['replace'] else 'no'}",
        "- Changed fields:",
    ]
    if report["workspace"]:
        lines.insert(4, f"- Workspace: {report['workspace']}")
    if report["changed_fields"]:
        for field in report["changed_fields"]:
            lines.append(f"  - {field}")
    else:
        lines.append("  - (none)")

    lines.append("- Preferences:")
    for key, value in report["preferences"].items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value
        lines.append(f"  - {key}: {rendered}")

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
        lines.append("- Migration: normalized a legacy workspace preferences file into the unified canonical format")
    if report["migrated_legacy_global_preferences"]:
        lines.append("- Migration: converted legacy global preferences state into a single unified preferences file")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(
        description="Preview or write host-neutral Forge preferences in the canonical per-scope preferences file."
    )
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root for workspace-scoped preferences")
    parser.add_argument(
        "--forge-home",
        type=Path,
        default=None,
        help="Override adapter state root (defaults to $FORGE_HOME, installed adapter state, bundle-native dev state, or ~/.forge only when no bundle-specific fallback exists)",
    )
    parser.add_argument("--scope", choices=["global", "workspace", "both"], default="global", help="Persistence scope")
    parser.add_argument("--technical-level", dest="technical_level", help="technical_level value or alias")
    parser.add_argument("--detail-level", dest="detail_level", help="detail_level value or alias")
    parser.add_argument("--autonomy-level", dest="autonomy_level", help="autonomy_level value or alias")
    parser.add_argument("--pace", help="pace value or alias")
    parser.add_argument("--feedback-style", dest="feedback_style", help="feedback_style value or alias")
    parser.add_argument("--personality", help="personality value or alias")
    parser.add_argument("--language", help="Optional output language hint")
    parser.add_argument("--orthography", help="Optional orthography hint")
    parser.add_argument("--tone-detail", dest="tone_detail", help="Optional tone detail or honorific hint")
    parser.add_argument("--output-quality", dest="output_quality", help="Optional output quality hint")
    parser.add_argument(
        "--custom-rule",
        dest="custom_rules",
        action="append",
        default=None,
        help="Append a custom rule. Repeat for multiple rules.",
    )
    parser.add_argument(
        "--clear-field",
        action="append",
        default=None,
        help="Remove a persisted canonical field from the selected scope. Repeat for multiple fields.",
    )
    parser.add_argument("--clear-language", action="store_true", help="Compatibility alias for --clear-field language")
    parser.add_argument("--clear-orthography", action="store_true", help="Compatibility alias for --clear-field orthography")
    parser.add_argument("--replace", action="store_true", help="Clear the target scope before applying explicit updates")
    parser.add_argument("--apply", action="store_true", help="Write the selected preferences instead of preview only")
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
