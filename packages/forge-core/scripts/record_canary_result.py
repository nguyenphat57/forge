from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug


VALID_STATUSES = ("pass", "warn", "fail")


def build_report(args: argparse.Namespace) -> dict:
    return {
        "workspace": args.workspace,
        "summary": args.summary,
        "status": args.status,
        "host": args.host,
        "scenarios": args.scenario,
        "signals": args.signal,
        "blockers": args.blocker,
        "follow_ups": args.follow_up,
        "observed_at": datetime.now().isoformat(timespec="seconds"),
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Canary Result",
        f"- Workspace: {report['workspace']}",
        f"- Status: {report['status']}",
        f"- Host: {report['host']}",
        f"- Observed at: {report['observed_at']}",
        f"- Summary: {report['summary']}",
    ]
    for label, items in (
        ("Scenarios", report["scenarios"]),
        ("Signals", report["signals"]),
        ("Blockers", report["blockers"]),
        ("Follow-ups", report["follow_ups"]),
    ):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "canary-runs") / slugify(report["workspace"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['summary'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record a Forge canary or soak-test result.")
    parser.add_argument("summary", help="Short outcome summary for this canary run")
    parser.add_argument("--workspace", required=True, help="Workspace label or repo name")
    parser.add_argument("--status", choices=VALID_STATUSES, required=True, help="Overall canary outcome")
    parser.add_argument("--host", default="generic", help="Host/runtime where the canary was observed")
    parser.add_argument("--scenario", action="append", default=[], help="Scenario or prompt cluster exercised. Repeatable.")
    parser.add_argument("--signal", action="append", default=[], help="Positive or cautionary observation. Repeatable.")
    parser.add_argument("--blocker", action="append", default=[], help="Blocking issue. Repeatable.")
    parser.add_argument("--follow-up", action="append", default=[], help="Follow-up action. Repeatable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist under .forge-artifacts/canary-runs")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted canary result:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
