from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _version_parts(value: str, *, upper: bool = False) -> tuple[int, int, int]:
    parts: list[int] = []
    for raw in value.split(".")[:3]:
        token = raw.strip().lower()
        if token in {"x", "*"}:
            parts.append(999999 if upper else 0)
            continue
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(999999 if upper else 0)
    while len(parts) < 3:
        parts.append(999999 if upper else 0)
    return tuple(parts[:3])


def _version_in_range(version: str, minimum: str | None, maximum: str | None) -> bool:
    current = _version_parts(version)
    if minimum and current < _version_parts(minimum):
        return False
    if maximum and current > _version_parts(maximum, upper=True):
        return False
    return True


def load_install_manifest(target: Path) -> dict[str, object] | None:
    manifest_path = target / "INSTALL-MANIFEST.json"
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def load_companion_compatibility(source_path: Path) -> tuple[str | None, dict[str, object] | None]:
    capabilities_path = source_path / "data" / "companion-capabilities.json"
    if not capabilities_path.exists():
        return None, None
    payload = json.loads(capabilities_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None, None
    version = str(payload.get("version") or "unknown")
    bounds = payload.get("compatibility")
    return version, bounds if isinstance(bounds, dict) else None


def build_companion_compatibility(*, core_version: str, companion_version: str, bounds: dict[str, object] | None) -> dict[str, object]:
    minimum = str(bounds.get("forge_core_min")) if isinstance(bounds, dict) and bounds.get("forge_core_min") else None
    maximum = str(bounds.get("forge_core_max")) if isinstance(bounds, dict) and bounds.get("forge_core_max") else None
    compatible = _version_in_range(core_version, minimum, maximum)
    if minimum and maximum:
        range_text = f"{minimum} - {maximum}"
    elif minimum:
        range_text = f">= {minimum}"
    elif maximum:
        range_text = f"<= {maximum}"
    else:
        range_text = "unbounded"
    return {
        "status": "PASS" if compatible else "WARN",
        "compatible": compatible,
        "core_version": core_version,
        "companion_version": companion_version,
        "bounds": {
            "forge_core_min": minimum,
            "forge_core_max": maximum,
            "range_text": range_text,
        },
        "message": (
            f"forge-core {core_version} is compatible with companion {companion_version}."
            if compatible
            else f"forge-core {core_version} is outside the supported range {range_text} for companion {companion_version}."
        ),
    }


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
    if report["codex_runtime_registration"]["enabled"]:
        manifest["codex_runtime_registration"] = report["codex_runtime_registration"]
    if report["gemini_runtime_registration"]["enabled"]:
        manifest["gemini_runtime_registration"] = report["gemini_runtime_registration"]
    if report["codex_companion_registration"]["enabled"]:
        manifest["codex_companion_registration"] = report["codex_companion_registration"]
    if report["gemini_companion_registration"]["enabled"]:
        manifest["gemini_companion_registration"] = report["gemini_companion_registration"]
    (target / "INSTALL-MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def format_text(report: dict) -> str:
    lines = [f"Forge Install ({report['bundle']})"]
    lines.append(f"- Mode: {report.get('mode', 'install')}")
    lines.append(f"- Version: {report['version']}")
    lines.append(f"- Host: {report['host']}")
    lines.append(f"- Source: {report['source']}")
    lines.append(f"- Target: {report['target']}")
    lines.append(f"- Dry run: {'yes' if report['dry_run'] else 'no'}")
    if report["compatibility"] is not None:
        compatibility = report["compatibility"]
        lines.append(f"- Compatibility: {compatibility['status']} - {compatibility['message']}")
    if report["transition"] is not None:
        transition = report["transition"]
        lines.append(f"- Transition: {transition['status']} - {transition['message']}")
    if report["backup_enabled"]:
        lines.append(f"- Backup: {report['backup_path'] or '(not needed)'}")
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
        lines.append(f"- Host backup: {activation['host_backup_path'] or '(not needed)'}")
    if report["gemini_host_activation"]["enabled"]:
        activation = report["gemini_host_activation"]
        lines.append("- Gemini host activation: yes")
        lines.append(f"- Gemini home: {activation['gemini_home']}")
        lines.append(f"- Global GEMINI: {activation['gemini_md_path']}")
        lines.append(f"- Host backup: {activation['host_backup_path'] or '(not needed)'}")
    if report["codex_runtime_registration"]["enabled"]:
        lines.append("- Codex runtime registration: yes")
        lines.append(f"- Codex runtime registry: {report['codex_runtime_registration']['registry_path']}")
    if report["gemini_runtime_registration"]["enabled"]:
        lines.append("- Gemini runtime registration: yes")
        lines.append(f"- Gemini runtime registry: {report['gemini_runtime_registration']['registry_path']}")
    if report["codex_companion_registration"]["enabled"]:
        lines.append("- Codex companion registration: yes")
        lines.append(f"- Codex companion registry: {report['codex_companion_registration']['registry_path']}")
    if report["codex_companion_registration"].get("message") and report["codex_companion_registration"].get("status") != "skipped":
        lines.append(f"- Codex companion note: {report['codex_companion_registration']['message']}")
    if report["gemini_companion_registration"]["enabled"]:
        lines.append("- Gemini companion registration: yes")
        lines.append(f"- Gemini companion registry: {report['gemini_companion_registration']['registry_path']}")
    if report["gemini_companion_registration"].get("message") and report["gemini_companion_registration"].get("status") != "skipped":
        lines.append(f"- Gemini companion note: {report['gemini_companion_registration']['message']}")
    return "\n".join(lines)
