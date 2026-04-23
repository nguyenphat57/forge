from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio


SECTION_RULES = {
    "source_of_truth": {
        "markers": ("Source of truth", "Sources:"),
        "question": "Which plan/spec/design artifact is the source of truth for this packet?",
    },
    "first_slice": {
        "markers": ("First slice", "Current slice", "Slice 1"),
        "question": "Which exact first slice should implementation start with?",
    },
    "baseline_verification": {
        "markers": ("Baseline", "Baseline verification"),
        "question": "Which baseline command or reproduction proves the packet starts from a known state?",
    },
    "proof_before_progress": {
        "markers": ("Proof before progress", "Proof:"),
        "question": "Which proof-before-progress check closes the current slice?",
    },
    "reopen_conditions": {
        "markers": ("Reopen only if", "Reopen if"),
        "question": "When should this packet reopen upstream instead of continuing build?",
    },
}
UNRESOLVED_MARKERS = ("TBD", "TODO", "[clarify]", "?", "to decide")


def _load_sources(paths: list[Path]) -> dict[str, str]:
    if not paths:
        raise ValueError("check-spec-packet needs at least one --source file.")
    return {str(path): path.read_text(encoding="utf-8") for path in paths}


def build_report(args: argparse.Namespace) -> dict:
    texts = _load_sources(args.source)
    combined = "\n".join(texts.values())
    missing_sections = [
        name
        for name, config in SECTION_RULES.items()
        if not any(marker in combined for marker in config["markers"])
    ]
    unresolved_lines = [
        line.strip()
        for line in combined.splitlines()
        if line.strip() and any(marker.lower() in line.lower() for marker in UNRESOLVED_MARKERS)
    ]
    clarification_question = None
    if missing_sections:
        clarification_question = SECTION_RULES[missing_sections[0]]["question"]
    elif unresolved_lines:
        clarification_question = f"What exact decision resolves this packet gap: {unresolved_lines[0]}?"

    status = "PASS"
    if len(missing_sections) >= 2:
        status = "FAIL"
    elif missing_sections or unresolved_lines:
        status = "WARN"

    return {
        "status": status,
        "sources": list(texts.keys()),
        "missing_sections": missing_sections,
        "unresolved_lines": unresolved_lines,
        "clarification_question": clarification_question,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Spec Packet Check",
        f"- Status: {report['status']}",
        f"- Sources: {', '.join(report['sources'])}",
        f"- Missing sections: {', '.join(report['missing_sections']) or '(none)'}",
    ]
    if report["unresolved_lines"]:
        lines.append("- Unresolved lines:")
        for item in report["unresolved_lines"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Unresolved lines: (none)")
    lines.append(f"- Clarification needed: {report['clarification_question'] or '(none)'}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Check whether a Forge plan/spec packet is ready enough for build.")
    parser.add_argument("--source", type=Path, action="append", default=[], help="Packet or plan/spec file. Repeatable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Spec Packet Check", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
