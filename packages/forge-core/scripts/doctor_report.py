from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, timestamp_slug


def _core_only_ready(checks: list[dict]) -> bool:
    return not any(check["status"] == "FAIL" for check in checks)


def _doctor_next_actions(workspace: Path, report: dict) -> list[str]:
    actions: list[str] = []
    if report["status"] == "FAIL":
        actions.append("Resolve the current doctor blockers, then rerun `doctor.py`.")
    elif report["warnings"]:
        actions.append("Resolve the current warnings that affect this repo, then rerun `doctor.py`.")
    actions.append(f"Run `map_codebase.py --workspace {workspace}` to capture a durable brownfield summary before editing.")
    actions.append("Use `help` or `next` after the map is recorded to choose the first concrete slice.")
    return actions


def build_doctor_report(workspace: Path, checks: list[dict]) -> dict:
    blockers = [check["label"] for check in checks if check["status"] == "FAIL"]
    warnings = [check["label"] for check in checks if check["status"] == "WARN"]
    remediations: list[str] = []
    for status in ("FAIL", "WARN"):
        for check in checks:
            remediation = str(check.get("remediation") or "").strip()
            if check["status"] == status and remediation and remediation not in remediations:
                remediations.append(remediation)
    status = "FAIL" if blockers else "WARN" if warnings else "PASS"
    report = {
        "status": status,
        "workspace": str(workspace),
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "remediations": remediations,
        "timestamp": timestamp_slug(),
    }
    report["core_only_ready"] = _core_only_ready(checks)
    report["next_actions"] = _doctor_next_actions(workspace, report)
    return report


def format_doctor_text(report: dict) -> str:
    lines = [
        "Forge Doctor",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Core-only path: {'ready' if report.get('core_only_ready') else 'blocked'}",
        "- Checks:",
    ]
    for check in report["checks"]:
        lines.append(f"  - [{check['status']}] {check['label']}: {check['detail']}")
    for label, items in (("Blockers", report["blockers"]), ("Warnings", report["warnings"]), ("Remediations", report["remediations"])):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")
    companions = report.get("companions")
    if isinstance(companions, list):
        lines.append("- Optional companions:")
        if companions:
            for item in companions:
                install_state = "registered" if item.get("registered") else "local"
                profile = item.get("operator_profile") or "(none)"
                pack = item.get("verification_pack") or "(none)"
                lines.append(f"  - {item['id']} ({item['strength']}, {install_state}, profile={profile}, pack={pack})")
        else:
            lines.append("  - (none)")
    companion_registry = report.get("companion_registry")
    if isinstance(companion_registry, dict):
        lines.append(f"- Optional companion registry path: {companion_registry['path']}")
        registered = companion_registry.get("registered_companions")
        lines.append(f"- Registered optional companions: {len(registered) if isinstance(registered, list) else 0}")
    artifacts = report.get("artifacts")
    if isinstance(artifacts, dict):
        lines.append("- Artifacts:")
        lines.append(f"  - JSON: {artifacts['json']}")
    lines.append("- Brownfield next steps:")
    for item in report.get("next_actions", []):
        lines.append(f"  - {item}")
    return "\n".join(lines)


def persist_doctor_report(report: dict, output_dir: str | None) -> Path:
    artifact_dir = default_artifact_dir(output_dir, "doctor")
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / f"{report['timestamp']}.json"
    latest_path = artifact_dir / "latest.json"
    history_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return latest_path
