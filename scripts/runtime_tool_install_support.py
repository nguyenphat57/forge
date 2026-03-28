from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_SCRIPTS_DIR = ROOT_DIR / "packages" / "forge-core" / "scripts"

if str(CORE_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_SCRIPTS_DIR))

from runtime_tool_support import available_runtime_tool_names, write_runtime_tool_registration


def _resolve_host_runtime_registry_path(
    host: str,
    *,
    codex_home: str | None = None,
    gemini_home: str | None = None,
) -> Path:
    if host == "codex":
        home = Path(codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
        return (home.expanduser().resolve() / "forge-codex" / "state" / "runtime-tools.json").resolve()
    if host == "gemini":
        home = Path(gemini_home or os.environ.get("GEMINI_HOME") or (Path.home() / ".gemini"))
        return (home.expanduser().resolve() / "forge-antigravity" / "state" / "runtime-tools.json").resolve()
    raise ValueError(f"Unsupported runtime-tool registry host: {host}")


def _empty_registration(host: str) -> dict[str, object]:
    return {"enabled": False, "host": host, "registry_path": None, "record": None}


def plan_runtime_tool_registrations(
    bundle_name: str,
    *,
    register_codex_runtime: bool,
    codex_home: str | None,
    register_gemini_runtime: bool,
    gemini_home: str | None,
) -> dict[str, dict[str, object]]:
    runtime_bundles = set(available_runtime_tool_names())
    if bundle_name not in runtime_bundles:
        return {"codex": _empty_registration("codex"), "gemini": _empty_registration("gemini")}

    registrations = {"codex": _empty_registration("codex"), "gemini": _empty_registration("gemini")}
    if register_codex_runtime:
        registrations["codex"] = {
            "enabled": True,
            "host": "codex",
            "registry_path": str(_resolve_host_runtime_registry_path("codex", codex_home=codex_home)),
            "record": None,
        }
    if register_gemini_runtime:
        registrations["gemini"] = {
            "enabled": True,
            "host": "gemini",
            "registry_path": str(_resolve_host_runtime_registry_path("gemini", gemini_home=gemini_home)),
            "record": None,
        }
    return registrations


def apply_runtime_tool_registrations(report: dict) -> None:
    for key in ("codex_runtime_registration", "gemini_runtime_registration"):
        registration = report.get(key)
        if not isinstance(registration, dict) or not registration.get("enabled"):
            continue
        registry_path = Path(str(registration["registry_path"]))
        registration["record"] = write_runtime_tool_registration(registry_path, report["bundle"], report["target"])
