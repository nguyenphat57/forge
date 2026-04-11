from __future__ import annotations

import argparse
import json

from skill_bundle_composer import adapter_skill_specs, ensure_generated_overlay_skills


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify checked-in adapter overlay SKILL.md artifacts.")
    parser.add_argument("--check", action="store_true", help="Fail if any generated overlay SKILL.md is stale.")
    parser.add_argument("--apply", action="store_true", help="Rewrite generated overlay SKILL.md files in place.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    if args.check == args.apply:
        raise SystemExit("Choose exactly one of --check or --apply.")

    report = ensure_generated_overlay_skills(check=args.check)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        lines = ["Generated Overlay Skills"]
        for artifact in report["artifacts"]:
            status = "STALE" if artifact["stale"] else "OK"
            lines.append(f"- [{status}] {artifact['bundle']} -> {artifact['output_path']}")
        print("\n".join(lines))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
