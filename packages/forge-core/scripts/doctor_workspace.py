from __future__ import annotations

import json
from pathlib import Path

from common import load_preferences, load_registry
from help_next_support import collect_repo_signals


def _write_access_check(workspace: Path) -> dict:
    artifact_root = workspace / ".forge-artifacts"
    probe_file = artifact_root / ".doctor-write-check"
    try:
        artifact_root.mkdir(parents=True, exist_ok=True)
        probe_file.write_text("ok\n", encoding="utf-8")
        probe_file.unlink()
        return {
            "id": "artifact-write-access",
            "label": "Artifact write access",
            "category": "workspace",
            "status": "PASS",
            "detail": f"Writable: {artifact_root}",
            "remediation": "",
        }
    except OSError as exc:
        return {
            "id": "artifact-write-access",
            "label": "Artifact write access",
            "category": "workspace",
            "status": "FAIL",
            "detail": str(exc),
            "remediation": "Fix workspace permissions or remove the conflicting `.forge-artifacts` path.",
        }


def collect_workspace_checks(workspace: Path) -> list[dict]:
    checks: list[dict] = []
    checks.append(
        {
            "id": "workspace-root",
            "label": "Workspace root",
            "category": "workspace",
            "status": "PASS" if workspace.exists() and workspace.is_dir() else "FAIL",
            "detail": f"Workspace: {workspace}",
            "remediation": "" if workspace.exists() and workspace.is_dir() else "Use a valid workspace directory.",
        }
    )
    signals = collect_repo_signals(workspace)
    checks.append(
        {
            "id": "workspace-markers",
            "label": "Workspace markers",
            "category": "workspace",
            "status": "PASS" if signals else "WARN",
            "detail": ", ".join(signals) if signals else "No README, manifest, docs, src, app, or tests markers found.",
            "remediation": "" if signals else "Confirm the workspace root is correct or add basic project markers like README or manifests.",
        }
    )
    preferences_report = load_preferences(workspace=workspace)
    preference_detail = f"Source: {preferences_report['source']['type']}"
    if preferences_report["warnings"]:
        preference_detail = preference_detail + " | " + "; ".join(preferences_report["warnings"])
    checks.append(
        {
            "id": "preferences-state",
            "label": "Preferences state",
            "category": "workspace",
            "status": "WARN" if preferences_report["warnings"] else "PASS",
            "detail": preference_detail,
            "remediation": "" if not preferences_report["warnings"] else "Repair malformed preference files or remove invalid values.",
        }
    )
    try:
        registry = load_registry()
        registry_valid = isinstance(registry.get("intents"), dict) and bool(registry["intents"])
        registry_detail = f"Loaded registry with {len(registry.get('intents', {}))} intents."
        registry_status = "PASS" if registry_valid else "FAIL"
        registry_fix = "" if registry_valid else "Repair the Forge routing registry data."
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        registry_detail = str(exc)
        registry_status = "FAIL"
        registry_fix = "Repair the Forge routing registry so routing and workflows can load."
    checks.append(
        {
            "id": "bundle-registry",
            "label": "Forge bundle registry",
            "category": "workspace",
            "status": registry_status,
            "detail": registry_detail,
            "remediation": registry_fix,
        }
    )
    checks.append(_write_access_check(workspace))
    return checks
