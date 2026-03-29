from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, timestamp_slug


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
    return {
        "status": status,
        "workspace": str(workspace),
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "remediations": remediations,
        "timestamp": timestamp_slug(),
    }


def format_doctor_text(report: dict) -> str:
    lines = [
        "Forge Doctor",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
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
        lines.append("- Companions:")
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
        lines.append(f"- Companion registry path: {companion_registry['path']}")
        registered = companion_registry.get("registered_companions")
        lines.append(f"- Registered companions: {len(registered) if isinstance(registered, list) else 0}")
    artifacts = report.get("artifacts")
    if isinstance(artifacts, dict):
        lines.append("- Artifacts:")
        lines.append(f"  - JSON: {artifacts['json']}")
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
