from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, read_text, slugify, timestamp_slug


REQUIRED_HEADINGS = [
    "## Summary",
    "## Objective",
    "## Required Sections",
    "## Pattern Focus",
    "## Runtime Focus",
    "## Anti-Patterns To Reject",
    "## Expected Deliverables",
    "## Review Prompts",
]


def resolve_master_path(path: Path) -> Path:
    if path.is_file():
        return path
    return path / "MASTER.md"


def resolve_surface_override(path: Path, surface: str | None) -> Path | None:
    if surface is None or path.is_file():
        return None
    return path / "surfaces" / f"{slugify(surface)}.md"


def add(findings: list[dict], level: str, code: str, message: str) -> None:
    findings.append({"level": level, "code": code, "message": message})


def build_report(target: Path, master_path: Path, surface_path: Path | None, findings: list[dict]) -> dict:
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
        "target": str(target),
        "master": str(master_path),
        "surface_override": str(surface_path) if surface_path else None,
        "status": status,
        "counts": counts,
        "findings": findings,
    }


def check_brief(args: argparse.Namespace) -> dict:
    target = args.path.resolve()
    master_path = resolve_master_path(target)
    surface_path = resolve_surface_override(target, args.surface)
    findings: list[dict] = []

    if not master_path.exists():
        add(findings, "fail", "missing_master", f"MASTER backend brief not found at {master_path}")
        return build_report(target, master_path, surface_path, findings)

    content = read_text(master_path)
    add(findings, "pass", "master_present", f"Using master brief: {master_path}")

    for heading in REQUIRED_HEADINGS:
        if heading in content:
            add(findings, "pass", "heading_present", f"Found required heading `{heading}`")
        else:
            add(findings, "fail", "heading_missing", f"Missing required heading `{heading}`")

    if "- Surface:" in content and "- Pattern:" in content and "- Runtime:" in content:
        add(findings, "pass", "metadata_present", "Master brief exposes surface/pattern/runtime metadata.")
    else:
        add(findings, "warn", "metadata_missing", "Master brief does not clearly expose surface/pattern/runtime metadata.")

    if args.surface:
        if surface_path and surface_path.exists():
            add(findings, "pass", "surface_present", f"Surface override found: {surface_path}")
            surface_content = read_text(surface_path)
            if "## Scope Override" in surface_content and "## Contract Notes" in surface_content:
                add(findings, "pass", "surface_sections_present", "Surface override has the expected sections.")
            else:
                add(findings, "warn", "surface_sections_missing", "Surface override exists but misses expected sections.")
        else:
            add(findings, "warn", "surface_missing", f"Expected surface override missing for `{args.surface}`.")

    return build_report(target, master_path, surface_path, findings)


def format_text(report: dict) -> str:
    lines = [
        "Forge Backend Brief Check",
        f"- Target: {report['target']}",
        f"- Master: {report['master']}",
        f"- Surface override: {report['surface_override'] or '(none)'}",
        f"- Status: {report['status']}",
        f"- Counts: pass={report['counts']['pass']} warn={report['counts']['warn']} fail={report['counts']['fail']}",
        "- Findings:",
    ]
    for item in report["findings"]:
        lines.append(f"  - [{item['level'].upper()}] {item['message']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "backend-brief-checks")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(Path(report['target']).name)}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Validate a persisted backend brief.")
    parser.add_argument("path", type=Path, help="Path to MASTER.md or the artifact directory containing MASTER.md")
    parser.add_argument("--surface", default=None, help="Optional endpoint/job/event name to validate")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist report under .forge-artifacts/backend-brief-checks")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = check_brief(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted backend brief check:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
