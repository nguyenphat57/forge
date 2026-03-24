from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify


STACK_PROFILES = {
    "generic-web": {
        "focus": [
            "Preserve the existing design system and tokens before inventing new visual language.",
            "Define layout, states, and responsive behavior before coding.",
            "Prefer semantic structure and clear interaction cues."
        ],
        "watchouts": [
            "Do not hide critical content behind sticky or fixed elements.",
            "Do not rely on color alone for status or affordance."
        ]
    },
    "html-tailwind": {
        "focus": [
            "Keep class composition readable; extract repeated patterns instead of building class soup.",
            "Use design tokens or CSS variables behind Tailwind theme values where possible.",
            "Stabilize hover and focus states without layout shift."
        ],
        "watchouts": [
            "Avoid arbitrary values everywhere when a token should exist.",
            "Avoid `transition-all` and overly transparent light-mode surfaces."
        ]
    },
    "react-vite": {
        "focus": [
            "Keep component boundaries aligned with screen regions and state ownership.",
            "Model loading, empty, and error states explicitly in the UI brief.",
            "Prefer responsive layouts that degrade cleanly from tablet/desktop to mobile."
        ],
        "watchouts": [
            "Do not hide expensive rerenders behind animation polish.",
            "Do not couple layout decisions to transient component state without reason."
        ]
    },
    "nextjs": {
        "focus": [
            "Define server/client boundaries before detailing component behavior.",
            "Account for loading and streaming placeholders in the visual plan.",
            "Treat image, typography, and route transitions as part of the UX contract."
        ],
        "watchouts": [
            "Do not design interactions that depend on client-only state without fallback.",
            "Do not let hydration edge cases dictate visual complexity."
        ]
    },
    "mobile-webview": {
        "focus": [
            "Design for touch first: large targets, stable reach zones, safe-area awareness.",
            "Plan keyboard, viewport resize, and background/resume behavior up front.",
            "Prefer simple motion and resilient layouts under constrained device performance."
        ],
        "watchouts": [
            "Do not put key actions at edges that collide with gestures or safe areas.",
            "Do not assume desktop hover or precise pointer interaction exists."
        ]
    }
}


PLATFORM_PROFILES = {
    "web": [
        "Primary breakpoints: 375px, 768px, 1024px, 1440px.",
        "Keyboard and focus behavior must stay usable."
    ],
    "mobile": [
        "Touch targets should stay >= 44px.",
        "Account for safe areas, on-screen keyboard, and reduced motion."
    ],
    "tablet": [
        "Optimize split layouts and thumb reach for landscape usage.",
        "Preserve information density without shrinking targets below touch comfort."
    ],
    "cross-platform": [
        "Document what remains shared and what diverges by platform.",
        "Check navigation, spacing, and gesture assumptions separately by form factor."
    ]
}


MODE_PROFILES = {
    "frontend": {
        "title": "Frontend Brief",
        "objective": "Translate UI requirements into an implementation-safe frontend plan before code.",
        "sections": [
            "Visual direction and design-system constraints",
            "Screens/components in scope",
            "State model: default, loading, empty, error, success",
            "Responsive behavior and layout rules",
            "Accessibility requirements",
            "Stack-specific implementation notes"
        ],
        "deliverables": [
            "Updated screen/component implementation",
            "Verification notes for responsive and accessibility checks"
        ],
        "anti_patterns": [
            "Introducing a new visual language without checking the existing design system",
            "Using emoji as UI icons",
            "Hover effects that shift layout or hide weak affordance",
            "Missing loading, empty, or error states",
            "Invisible borders or unreadable text in light mode"
        ]
    },
    "visualize": {
        "title": "Visual Brief",
        "objective": "Clarify interaction model and visual direction before any UI code or mockup handoff.",
        "sections": [
            "Product/screen goal and user task",
            "Visual direction, tone, and references",
            "Screen map and interaction flow",
            "Component/state matrix",
            "Responsive and platform considerations",
            "Accessibility and motion boundaries"
        ],
        "deliverables": [
            "Text wireframe or mockup guidance",
            "Design spec or handoff notes for implementation"
        ],
        "anti_patterns": [
            "Jumping into components before the interaction model is clear",
            "Designing only the happy path and ignoring system states",
            "Assuming desktop-only interaction for touch-heavy surfaces",
            "Using motion without considering reduced-motion and readability"
        ]
    }
}


def build_brief(args: argparse.Namespace) -> dict:
    profile = MODE_PROFILES[args.mode]
    stack_profile = STACK_PROFILES[args.stack]
    platform_notes = PLATFORM_PROFILES[args.platform]
    project_name = args.project_name or Path.cwd().name

    return {
        "mode": args.mode,
        "title": profile["title"],
        "project_name": project_name,
        "screen": args.screen,
        "summary": args.summary,
        "stack": args.stack,
        "platform": args.platform,
        "objective": profile["objective"],
        "sections": profile["sections"],
        "deliverables": profile["deliverables"],
        "stack_focus": stack_profile["focus"],
        "stack_watchouts": stack_profile["watchouts"],
        "platform_notes": platform_notes,
        "anti_patterns": profile["anti_patterns"],
        "notes": args.note,
    }


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

    lines.extend([
        "",
        "## Stack Focus",
    ])
    for item in brief["stack_focus"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Platform Notes",
    ])
    for item in brief["platform_notes"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Anti-Patterns To Reject",
    ])
    for item in brief["anti_patterns"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Stack Watchouts",
    ])
    for item in brief["stack_watchouts"]:
        lines.append(f"- {item}")

    if brief["notes"]:
        lines.extend([
            "",
            "## Notes",
        ])
        for item in brief["notes"]:
            lines.append(f"- {item}")

    lines.extend([
        "",
        "## Expected Deliverables",
    ])
    for item in brief["deliverables"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Review Prompts",
        "- Which states are easy to forget in this UI?",
        "- What would break first on mobile or tablet?",
        "- Which interaction cues would be too weak without explicit focus/hover treatment?",
        "- What needs a token instead of an ad-hoc style decision?",
    ])

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
        lines.extend([
            "",
            "## Extra Notes",
        ])
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


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Generate a frontend or visualize UI brief artifact.")
    parser.add_argument("summary", help="Task summary or design problem statement")
    parser.add_argument("--mode", choices=["frontend", "visualize"], required=True, help="Brief mode")
    parser.add_argument("--project-name", default=None, help="Project name for persisted artifacts")
    parser.add_argument("--screen", default=None, help="Optional screen/page name for page-specific override")
    parser.add_argument(
        "--stack",
        choices=sorted(STACK_PROFILES.keys()),
        default="generic-web",
        help="Implementation stack lens to apply",
    )
    parser.add_argument(
        "--platform",
        choices=sorted(PLATFORM_PROFILES.keys()),
        default="web",
        help="Primary platform lens",
    )
    parser.add_argument("--note", action="append", default=[], help="Extra note to include. Repeatable.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist to .forge-artifacts/ui-briefs/<project>/")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    brief = build_brief(args)
    if args.format == "json":
        print(json.dumps(brief, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(brief))

    if args.persist:
        written = persist_brief(brief, args.output_dir)
        print("\nPersisted UI brief artifacts:")
        for path in written:
            print(f"- {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
