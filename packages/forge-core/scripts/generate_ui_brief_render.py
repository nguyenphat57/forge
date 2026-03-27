from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, slugify


def format_markdown(brief: dict) -> str:
    screen_label = brief["screen"] or "shared"
    lines = [
        f"# {brief['title']}: {screen_label}",
        "",
        f"- Project: {brief['project_name']}",
        f"- Mode: {brief['mode']}",
        f"- Screen/Scope: {screen_label}",
        f"- Stack: {brief['stack']}",
        f"- Platform: {brief['platform']}",
        "",
        "## Summary",
        brief["summary"],
        "",
        "## Objective",
        brief["objective"],
        "",
        "## Required Sections",
    ]
    for item in brief["sections"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Stack Focus"])
    for item in brief["stack_focus"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Platform Notes"])
    for item in brief["platform_notes"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Anti-Patterns To Reject"])
    for item in brief["anti_patterns"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Stack Watchouts"])
    for item in brief["stack_watchouts"]:
        lines.append(f"- {item}")

    if brief["notes"]:
        lines.extend(["", "## Notes"])
        for item in brief["notes"]:
            lines.append(f"- {item}")

    lines.extend(["", "## Expected Deliverables"])
    for item in brief["deliverables"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Review Prompts",
            "- Which states are easy to forget in this UI?",
            "- What would break first on mobile or tablet?",
            "- Which interaction cues would be too weak without explicit focus/hover treatment?",
            "- What needs a token instead of an ad-hoc style decision?",
        ]
    )

    return "\n".join(lines) + "\n"


def format_override_markdown(brief: dict) -> str:
    screen_label = brief["screen"] or "shared"
    lines = [
        f"# Page Override: {screen_label}",
        "",
        f"- Project: {brief['project_name']}",
        f"- Stack: {brief['stack']}",
        f"- Platform: {brief['platform']}",
        "",
        "Use this file as a screen-specific override. `MASTER.md` remains the baseline source of truth.",
        "",
        "## Scope Override",
        brief["summary"],
        "",
        "## State/Interaction Notes",
        "- Document only what differs from the master brief.",
        "- Call out loading, empty, error, and destructive states if they diverge.",
        "",
        "## Layout/Responsive Notes",
        "- Note any breakpoint-specific changes or safe-area constraints unique to this screen.",
        "",
        "## Accessibility Notes",
        "- Focus order, accessible names, and reduced-motion differences for this screen.",
    ]
    if brief["notes"]:
        lines.extend(["", "## Extra Notes"])
        for item in brief["notes"]:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def persist_brief(brief: dict, output_dir: str | None) -> list[Path]:
    artifact_root = default_artifact_dir(output_dir, "ui-briefs") / slugify(brief["project_name"]) / brief["mode"]
    artifact_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    master_md = artifact_root / "MASTER.md"
    master_json = artifact_root / "MASTER.json"
    master_md.write_text(format_markdown(brief), encoding="utf-8")
    master_json.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    written.extend([master_md, master_json])

    if brief["screen"]:
        pages_dir = artifact_root / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        override_path = pages_dir / f"{slugify(brief['screen'])}.md"
        override_path.write_text(format_override_markdown(brief), encoding="utf-8")
        written.append(override_path)

    return written
