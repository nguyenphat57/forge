from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import record_canary_result
from common import default_artifact_dir, slugify, timestamp_slug


def format_text(report: dict) -> str:
    lines = [
        "Forge Workspace Canary",
        f"- Workspace: {report['workspace_name']} ({report['workspace']})",
        f"- Status: {report['status']}",
        f"- Repo signals: {', '.join(report['repo_signals']) or '(none)'}",
        f"- Runtimes: {', '.join(report['runtimes']) or '(none)'}",
        f"- Workspace router: {report['workspace_router'] or '(none)'}",
        f"- Summary: {report['summary']}",
        "- Scenarios:",
    ]
    for scenario in report["scenarios"]:
        lines.append(
            "  - [{status}] {name}: {intent}".format(
                status=scenario["status"],
                name=scenario["name"],
                intent=scenario["detected"]["intent"],
            )
        )
        if scenario["failures"]:
            for failure in scenario["failures"]:
                lines.append(f"    - {failure}")
    if report["router_check"] is None:
        lines.append("- Router check: skipped")
    else:
        lines.append(f"- Router check: {report['router_check']['status']}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    if report["blockers"]:
        lines.append("- Blockers:")
        for item in report["blockers"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Blockers: (none)")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "workspace-canaries") / slugify(report["workspace_name"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['workspace_name'])}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    latest_json = artifact_dir / "latest.json"
    latest_md = artifact_dir / "latest.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_md.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def persist_canary_result(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    result = record_canary_result.build_report(
        Namespace(
            workspace=report["workspace_name"],
            summary=report["summary"],
            status=report["status"],
            host="generic",
            scenario=[scenario["name"] for scenario in report["scenarios"]],
            signal=[
                "Repo signals: {signals}".format(signals=", ".join(report["repo_signals"]) or "(none)"),
                "Workspace router: {router}".format(router=report["workspace_router"] or "(none)"),
            ],
            blocker=report["blockers"],
            follow_up=report["warnings"],
        )
    )
    return record_canary_result.persist_report(result, output_dir)
