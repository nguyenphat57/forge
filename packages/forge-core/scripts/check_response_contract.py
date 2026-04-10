from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, load_preferences, resolve_output_contract
from response_contract import validate_response_contract
from skill_routing import load_registry, registry_sources


def read_response_text(*, response_text: str | None, input_file: Path | None) -> str:
    if response_text:
        return response_text
    if input_file is None:
        raise ValueError("Provide --response-text or --input-file.")
    if not input_file.exists():
        raise FileNotFoundError(f"Response input file does not exist: {input_file}")
    return input_file.read_text(encoding="utf-8")


def build_output_contract(
    *,
    workspace: Path | None,
    forge_home: Path | None,
    preferences_file: Path | None,
    language: str | None,
    orthography: str | None,
) -> tuple[dict[str, object], dict[str, object]]:
    report = load_preferences(
        workspace=workspace,
        forge_home=forge_home,
        preferences_file=preferences_file,
    )
    extra = dict(report.get("extra", {}))
    if language:
        extra["language"] = language
    if orthography:
        extra["orthography"] = orthography
    return resolve_output_contract(extra), report["source"]


def format_text(report: dict[str, object]) -> str:
    lines = [
        "Forge Response Contract",
        f"- Status: {report['status']}",
        f"- Registry source: {report['registry_source']}",
        f"- Preferences source: {report['preferences_source']}",
        f"- Evidence response required: {report['evidence_required']}",
    ]
    if report["output_contract"]:
        lines.append("- Output contract:")
        for line in json.dumps(report["output_contract"], indent=2, ensure_ascii=False).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("- Output contract: (none)")

    checks = report["checks"]
    lines.append(f"- Evidence mode: {checks['evidence_response']['mode'] or '(none)'}")
    lines.append(
        f"- Skill usage footer: {checks['skill_usage_footer']['footer_line'] or '(missing)'}"
    )
    skills_used = checks["skill_usage_footer"]["skills"]
    lines.append(f"- Skills used: {', '.join(skills_used) or 'none'}")
    lines.append(f"- Banned phrases: {', '.join(checks['banned_phrases']) or '(none)'}")
    lines.append(
        f"- Rationalization patterns: {', '.join(checks['rationalization_patterns']) or '(none)'}"
    )
    if report["findings"]:
        lines.append("- Findings:")
        for finding in report["findings"]:
            lines.append(f"  - {finding}")
    else:
        lines.append("- Findings: (none)")
    if report["warnings"]:
        lines.append("- Warnings:")
        for warning in report["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Validate a Forge user-facing response against the active output contract.")
    parser.add_argument("--response-text", default=None, help="Inline response text to validate")
    parser.add_argument("--input-file", type=Path, default=None, help="Optional UTF-8 file containing response text")
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root for preference resolution")
    parser.add_argument("--forge-home", type=Path, default=None, help="Optional Forge home override")
    parser.add_argument("--preferences-file", type=Path, default=None, help="Explicit preferences file to resolve")
    parser.add_argument("--language", default=None, help="Override language for output contract validation")
    parser.add_argument("--orthography", default=None, help="Override orthography for output contract validation")
    parser.add_argument(
        "--require-evidence-response",
        action="store_true",
        help="Require the global evidence response structure even if the text does not claim completion.",
    )
    parser.add_argument(
        "--expected-skills",
        default=None,
        help="Optional comma-separated Forge skill names expected in the final `Skills used:` footer, or `none`.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        response_text = read_response_text(response_text=args.response_text, input_file=args.input_file)
        output_contract, preferences_source = build_output_contract(
            workspace=args.workspace,
            forge_home=args.forge_home,
            preferences_file=args.preferences_file,
            language=args.language,
            orthography=args.orthography,
        )
    except (FileNotFoundError, ValueError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Response Contract", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    registry = load_registry()
    expected_skills: list[str] | None = None
    if args.expected_skills is not None:
        token = args.expected_skills.strip()
        if token.casefold() == "none":
            expected_skills = []
        else:
            expected_skills = [part.strip() for part in token.split(",") if part.strip()]
    report = validate_response_contract(
        response_text,
        output_contract=output_contract,
        registry=registry,
        require_evidence_response=args.require_evidence_response,
        expected_skills=expected_skills,
    )
    payload = {
        **report,
        "registry_source": " + ".join(registry_sources()),
        "preferences_source": preferences_source["type"],
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(payload))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
