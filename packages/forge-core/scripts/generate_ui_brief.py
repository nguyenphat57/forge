from __future__ import annotations

import argparse
import json

from common import configure_stdio
from generate_ui_brief_profiles import MODE_PROFILES, PLATFORM_PROFILES, STACK_PROFILES, build_brief
from generate_ui_brief_render import format_markdown, format_override_markdown, persist_brief


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
