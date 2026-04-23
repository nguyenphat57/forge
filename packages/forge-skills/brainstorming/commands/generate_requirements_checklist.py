from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio


AMBIGUOUS_HINTS = ("fast", "easy", "simple", "intuitive", "quick", "etc", "maybe", "probably")
MEASURABLE_HINTS = ("must", "within", "before", "after", "at least", "at most", "when", "then")
TESTABLE_HINTS = ("test", "verify", "proof", "scenario", "reproduce", "assert", "check")


def _load_requirements(args: argparse.Namespace) -> list[str]:
    if args.requirement:
        return [item.strip() for item in args.requirement if item.strip()]
    if args.input_file:
        lines = args.input_file.read_text(encoding="utf-8").splitlines()
        return [line.strip("- ").strip() for line in lines if line.strip()]
    return []


def _check(text: str, hints: tuple[str, ...], *, fallback_digits: bool = False) -> bool:
    lowered = text.lower()
    if fallback_digits and any(char.isdigit() for char in text):
        return True
    return any(hint in lowered for hint in hints)


def build_report(args: argparse.Namespace) -> dict:
    requirements = _load_requirements(args)
    if not requirements:
        raise ValueError("Requirements checklist needs at least one requirement.")

    items: list[dict] = []
    warning_count = 0
    for text in requirements:
        ambiguity_pass = not _check(text, AMBIGUOUS_HINTS)
        measurability_pass = _check(text, MEASURABLE_HINTS, fallback_digits=True)
        testability_pass = _check(text, TESTABLE_HINTS) or "when " in text.lower()
        notes: list[str] = []
        if not ambiguity_pass:
            notes.append("Requirement uses ambiguous wording that needs sharpening.")
        if not measurability_pass:
            notes.append("Requirement is not measurable enough yet.")
        if not testability_pass:
            notes.append("Requirement does not describe a proof or repeatable scenario.")
        status = "PASS" if ambiguity_pass and measurability_pass and testability_pass else "WARN"
        if status != "PASS":
            warning_count += 1
        items.append(
            {
                "text": text,
                "status": status,
                "checks": {
                    "ambiguity": "PASS" if ambiguity_pass else "WARN",
                    "measurability": "PASS" if measurability_pass else "WARN",
                    "testability": "PASS" if testability_pass else "WARN",
                },
                "notes": notes,
            }
        )

    return {
        "status": "PASS" if warning_count == 0 else "WARN",
        "requirements": items,
        "summary": {"total": len(items), "warnings": warning_count},
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Requirements Checklist",
        f"- Status: {report['status']}",
        f"- Total requirements: {report['summary']['total']}",
        f"- Warnings: {report['summary']['warnings']}",
    ]
    for item in report["requirements"]:
        lines.append(f"- Requirement: {item['text']}")
        lines.append(f"  - Status: {item['status']}")
        for name, value in item["checks"].items():
            lines.append(f"  - {name}: {value}")
        if item["notes"]:
            for note in item["notes"]:
                lines.append(f"  - note: {note}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Generate a lightweight Forge requirements checklist.")
    parser.add_argument("--requirement", action="append", default=[], help="Requirement text. Repeatable.")
    parser.add_argument("--input-file", type=Path, default=None, help="Optional file with requirement lines.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Requirements Checklist", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
