from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, timestamp_slug
from dashboard_support import build_dashboard_report, format_dashboard_text


def persist_dashboard(report: dict, output_dir: str | None) -> Path:
    artifact_dir = default_artifact_dir(output_dir, "dashboard")
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = artifact_dir / "latest.json"
    history_path = history_dir / f"{timestamp_slug()}.json"
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    latest_path.write_text(payload, encoding="utf-8")
    history_path.write_text(payload, encoding="utf-8")
    return latest_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Render a terminal-first Forge dashboard from workspace artifacts.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist dashboard artifacts")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_dashboard_report(args.workspace.resolve())
    if args.persist:
        report["artifacts"] = {"json": str(persist_dashboard(report, args.output_dir or str(args.workspace.resolve())))}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_dashboard_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
