from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, read_text, slugify, timestamp_slug


REQUIRED_HEADINGS = {
    "frontend": [
        "## Summary",
        "## Objective",
        "## Required Sections",
        "## Stack Focus",
        "## Platform Notes",
        "## Anti-Patterns To Reject",
        "## Stack Watchouts",
        "## Expected Deliverables",
        "## Review Prompts",
    ],
    "visualize": [
        "## Summary",
        "## Objective",
        "## Required Sections",
        "## Stack Focus",
        "## Platform Notes",
        "## Anti-Patterns To Reject",
        "## Stack Watchouts",
        "## Expected Deliverables",
        "## Review Prompts",
    ],
}


def resolve_master_path(path: Path) -> Path:
    if path.is_file():
        return path
    mode_dirs = {"frontend", "visualize"}
    if path.name not in mode_dirs:
        for mode_dir in mode_dirs:
            candidate = path / mode_dir / "MASTER.md"
            if candidate.exists():
                return candidate
    master = path / "MASTER.md"
    return master


def resolve_page_override(path: Path, screen: str | None, mode: str) -> Path | None:
    if screen is None or path.is_file():
        return None
    if path.name != mode:
        mode_path = path / mode
        if mode_path.exists():
            path = mode_path
    return path / "pages" / f"{slugify(screen)}.md"


def add(findings: list[dict], level: str, code: str, message: str) -> None:
    findings.append({"level": level, "code": code, "message": message})


def check_brief(args: argparse.Namespace) -> dict:
    target = args.path.resolve()
    master_path = resolve_master_path(target)
    page_path = resolve_page_override(target, args.screen, args.mode)
    findings: list[dict] = []

    if not master_path.exists():
        add(findings, "fail", "missing_master", f"MASTER brief not found at {master_path}")
        return build_report(args.mode, target, master_path, page_path, findings)

    content = read_text(master_path)
    add(findings, "pass", "master_present", f"Using master brief: {master_path}")

    for heading in REQUIRED_HEADINGS[args.mode]:
        if heading in content:
            add(findings, "pass", "heading_present", f"Found required heading `{heading}`")
        else:
            add(findings, "fail", "heading_missing", f"Missing required heading `{heading}`")

    if "- Screen/Scope:" in content:
        add(findings, "pass", "scope_present", "Master brief records screen or scope.")
    else:
        add(findings, "warn", "scope_missing", "Master brief does not clearly expose screen/scope metadata.")

    if args.screen:
        if page_path and page_path.exists():
            add(findings, "pass", "page_present", f"Page override found: {page_path}")
            page_content = read_text(page_path)
            if "## Scope Override" in page_content and "## State/Interaction Notes" in page_content:
                add(findings, "pass", "page_sections_present", "Page override has the expected override sections.")
            else:
                add(findings, "warn", "page_sections_missing", "Page override exists but is missing one or more expected sections.")
        else:
            add(findings, "warn", "page_missing", f"Expected page override missing for screen `{args.screen}`.")

    return build_report(args.mode, target, master_path, page_path, findings)


def build_report(mode: str, target: Path, master_path: Path, page_path: Path | None, findings: list[dict]) -> dict:
    counts = {
        "pass": sum(1 for item in findings if item["level"] == "pass"),
        "warn": sum(1 for item in findings if item["level"] == "warn"),
        "fail": sum(1 for item in findings if item["level"] == "fail"),
    }
    if counts["fail"] > 0:
        status = "FAIL"
    elif counts["warn"] > 0:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "mode": mode,
        "target": str(target),
        "master": str(master_path),
        "page_override": str(page_path) if page_path else None,
        "status": status,
        "counts": counts,
        "findings": findings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge UI Brief Check",
        f"- Mode: {report['mode']}",
        f"- Target: {report['target']}",
        f"- Master: {report['master']}",
        f"- Page override: {report['page_override'] or '(none)'}",
        f"- Status: {report['status']}",
        f"- Counts: pass={report['counts']['pass']} warn={report['counts']['warn']} fail={report['counts']['fail']}",
        "- Findings:",
    ]
    for item in report["findings"]:
        lines.append(f"  - [{item['level'].upper()}] {item['message']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "ui-brief-checks")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(Path(report['target']).name)}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Validate a persisted frontend or visual brief.")
    parser.add_argument("path", type=Path, help="Path to MASTER.md or the artifact directory containing MASTER.md")
    parser.add_argument("--mode", choices=["frontend", "visualize"], required=True, help="Brief mode")
    parser.add_argument("--screen", default=None, help="Optional page override name to validate")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist report under .forge-artifacts/ui-brief-checks")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = check_brief(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted UI brief check:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
