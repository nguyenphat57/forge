from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load_install_manifest(target: Path) -> dict[str, object] | None:
    manifest_path = target / "INSTALL-MANIFEST.json"
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def build_install_transition(
    existing_install: dict | None,
    *,
    current_version: str,
    intent: str,
    bundle_sync_required: bool = True,
) -> dict[str, object]:
    if existing_install is None:
        return {
            "status": "inspect" if intent == "inspect" else "new-install",
            "previous_version": None,
            "current_version": current_version,
            "message": "Inspecting bundle source." if intent == "inspect" else "No existing install manifest found.",
        }
    previous_version = str(existing_install.get("version") or "unknown")
    if intent == "inspect":
        status = "inspect-existing"
        message = f"Existing install found at version {previous_version}."
    elif not bundle_sync_required:
        status = "already-current"
        message = f"Target already matches source bundle {current_version}; skipping file sync."
    elif intent == "upgrade":
        status = "upgrade"
        message = (
            f"Upgrading target from {previous_version} to {current_version}."
            if previous_version != current_version
            else f"Upgrade requested but target already has version {current_version}."
        )
    elif previous_version == current_version:
        status = "same-version"
        message = f"Target already has version {current_version}."
    else:
        status = "replace"
        message = f"Updating target from {previous_version} to {current_version}."
    return {
        "status": status,
        "previous_version": previous_version,
        "current_version": current_version,
        "message": message,
    }


def write_install_manifest(target: Path, report: dict) -> None:
    manifest = {
        "bundle": report["bundle"],
        "mode": report["mode"],
        "target": report["target"],
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": report["version"],
        "git_revision": report["git_revision"],
        "host": report["host"],
        "source": report["source"],
        "backup_path": report["backup_path"],
        "source_build_manifest": report["source_build_manifest"],
        "state": report["state"],
        "bundle_fingerprint": report["bundle_fingerprint"],
    }
    if report.get("compatibility") is not None:
        manifest["compatibility"] = report["compatibility"]
    if report.get("transition") is not None:
        manifest["transition"] = report["transition"]
    if report.get("sibling_skills") is not None:
        manifest["sibling_skills"] = report["sibling_skills"]
    if report["codex_host_activation"]["enabled"]:
        activation = report["codex_host_activation"]
        manifest["codex_host_activation"] = {
            "enabled": True,
            "codex_home": activation["codex_home"],
            "agents_path": activation["agents_path"],
            "host_backup_path": activation["host_backup_path"],
        }
    if report["gemini_host_activation"]["enabled"]:
        activation = report["gemini_host_activation"]
        manifest["gemini_host_activation"] = {
            "enabled": True,
            "gemini_home": activation["gemini_home"],
            "gemini_md_path": activation["gemini_md_path"],
            "host_backup_path": activation["host_backup_path"],
        }
    (target / "INSTALL-MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def format_text(report: dict) -> str:
    lines = [f"Forge Install ({report['bundle']})"]
    lines.append(f"- Mode: {report.get('mode', 'install')}")
    lines.append(f"- Version: {report['version']}")
    lines.append(f"- Host: {report['host']}")
    lines.append(f"- Source: {report['source']}")
    lines.append(f"- Target: {report['target']}")
    lines.append(f"- Dry run: {'yes' if report['dry_run'] else 'no'}")
    compatibility = report.get("compatibility")
    if compatibility is not None:
        lines.append(f"- Compatibility: {compatibility['status']} - {compatibility['message']}")
    transition = report.get("transition")
    if transition is not None:
        lines.append(f"- Transition: {transition['status']} - {transition['message']}")
    if report["backup_enabled"]:
        lines.append(f"- Backup snapshot: {report['backup_path'] or '(not needed)'}")
    if not report.get("bundle_sync_required", True):
        lines.append("- Bundle sync: skipped (target already matches source)")
    if report["codex_host_activation"]["enabled"]:
        activation = report["codex_host_activation"]
        lines.append("- Codex host activation: yes")
        lines.append(f"- Codex home: {activation['codex_home']}")
        lines.append(f"- Global AGENTS: {activation['agents_path']}")
        lines.append(f"- Retire legacy runtime: {activation['legacy_runtime_path']}")
        if activation["legacy_skill_paths"]:
            lines.append(f"- Retire legacy skills: {', '.join(activation['legacy_skill_paths'])}")
        lines.append(f"- Host snapshot: {activation['host_backup_path'] or '(not needed)'}")
    if report["gemini_host_activation"]["enabled"]:
        activation = report["gemini_host_activation"]
        lines.append("- Gemini host activation: yes")
        lines.append(f"- Gemini home: {activation['gemini_home']}")
        lines.append(f"- Global GEMINI: {activation['gemini_md_path']}")
        lines.append(f"- Host snapshot: {activation['host_backup_path'] or '(not needed)'}")
    sibling_skills = report.get("sibling_skills") or {}
    if sibling_skills.get("enabled"):
        skill_names = [item["name"] for item in sibling_skills.get("skills", [])]
        lines.append(f"- Sibling Forge skills: {', '.join(skill_names)}")
    return "\n".join(lines)
