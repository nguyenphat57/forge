from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_SCRIPTS_DIR = ROOT_DIR / "packages" / "forge-core" / "scripts"

if str(CORE_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_SCRIPTS_DIR))

from companion_registry import find_companion_record, load_companion_registry, write_companion_registration


def _resolve_host_companion_registry_path(host: str, *, codex_home: str | None = None, gemini_home: str | None = None) -> Path:
    if host == "codex":
        home = Path(codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
        return (home.expanduser().resolve() / "forge-codex" / "state" / "companions.json").resolve()
    if host == "gemini":
        home = Path(gemini_home or os.environ.get("GEMINI_HOME") or (Path.home() / ".gemini"))
        return (home.expanduser().resolve() / "forge-antigravity" / "state" / "companions.json").resolve()
    raise ValueError(f"Unsupported companion registry host: {host}")


def _empty_registration(host: str) -> dict[str, object]:
    return {"enabled": False, "host": host, "registry_path": None, "record": None, "status": "skipped", "message": None}


def _planned_registration(host: str, registry_path: str) -> dict[str, object]:
    return {
        "enabled": True,
        "host": host,
        "registry_path": registry_path,
        "record": None,
        "status": "planned",
        "message": f"Will register companion in {host} registry.",
    }


def plan_companion_registrations(
    bundle_name: str,
    *,
    bundle_host: str | None,
    register_codex_companion: bool,
    codex_home: str | None,
    register_gemini_companion: bool,
    gemini_home: str | None,
) -> dict[str, dict[str, object]]:
    registrations = {"codex": _empty_registration("codex"), "gemini": _empty_registration("gemini")}
    if bundle_host != "companion":
        if register_codex_companion or register_gemini_companion:
            reason = "Companion registration only applies to companion bundles."
            registrations["codex"]["status"] = "ignored"
            registrations["codex"]["message"] = reason
            registrations["gemini"]["status"] = "ignored"
            registrations["gemini"]["message"] = reason
        return registrations
    if register_codex_companion:
        registrations["codex"] = _planned_registration("codex", str(_resolve_host_companion_registry_path("codex", codex_home=codex_home)))
    if register_gemini_companion:
        registrations["gemini"] = _planned_registration("gemini", str(_resolve_host_companion_registry_path("gemini", gemini_home=gemini_home)))
    return registrations


def _describe_registration_transition(registry_path: Path, target: Path, package_name: str) -> tuple[str, str | None]:
    registry = load_companion_registry(registry_path)
    previous_record = find_companion_record(registry, package_name) if isinstance(registry, dict) else None
    if not isinstance(previous_record, dict):
        return "registered", None
    previous_target = Path(str(previous_record.get("target") or "")).expanduser().resolve()
    current_target = target.expanduser().resolve()
    if previous_target == current_target:
        return "refreshed", f"Registry already pointed at {current_target}."
    if not previous_target.exists():
        return "replaced-stale-path", f"Replaced stale registry target {previous_target} with {current_target}."
    return "replaced", f"Updated registry target from {previous_target} to {current_target}."


def apply_companion_registrations(report: dict) -> None:
    for key in ("codex_companion_registration", "gemini_companion_registration"):
        registration = report.get(key)
        if not isinstance(registration, dict) or not registration.get("enabled"):
            continue
        registry_path = Path(str(registration["registry_path"]))
        target = Path(str(report["target"]))
        registration["status"], registration["message"] = _describe_registration_transition(registry_path, target, str(report["bundle"]))
        registration["record"] = write_companion_registration(registry_path, target)
        if registration["status"] == "registered":
            registration["message"] = f"Registered companion at {target.resolve()}."
