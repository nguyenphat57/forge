from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from runtime_tool_support import available_runtime_tool_names, resolve_runtime_tool, resolve_runtime_tools_registry_path


def _runtime_health_check(bundle_name: str, resolution: dict) -> dict:
    if bundle_name != "forge-browse":
        return {
            "id": f"{bundle_name}-health",
            "label": f"{bundle_name} runtime health",
            "category": "runtime",
            "status": "PASS",
            "detail": f"Resolved at {resolution['target']}",
            "remediation": "",
        }
    completed = subprocess.run(
        [sys.executable, str(resolution["script_path"]), "doctor", "--format", "json"],
        cwd=str(Path(str(resolution["target"]))),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    detail = completed.stdout.strip() or completed.stderr.strip() or "No doctor output."
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
        detail = json.dumps(payload.get("checks", {}), ensure_ascii=False)
        status = "PASS" if payload.get("status") == "PASS" else "WARN"
    except json.JSONDecodeError:
        status = "WARN" if completed.returncode != 0 else "PASS"
    return {
        "id": f"{bundle_name}-health",
        "label": f"{bundle_name} runtime health",
        "category": "runtime",
        "status": status,
        "detail": detail,
        "remediation": "" if status == "PASS" else "Repair Playwright or the forge-browse runtime installation before browser QA.",
    }


def collect_runtime_checks() -> list[dict]:
    registry_path = resolve_runtime_tools_registry_path()
    checks = [
        {
            "id": "runtime-tool-registry",
            "label": "Runtime tool registry",
            "category": "runtime",
            "status": "PASS" if registry_path is not None else "WARN",
            "detail": str(registry_path) if registry_path is not None else "No runtime tool registry path resolved.",
            "remediation": "" if registry_path is not None else "Configure a runtime tool registry if you want optional runtime bundles to resolve automatically.",
        }
    ]
    for bundle_name in available_runtime_tool_names():
        resolution = resolve_runtime_tool(bundle_name)
        if resolution["status"] != "PASS":
            checks.append(
                {
                    "id": f"{bundle_name}-resolution",
                    "label": f"{bundle_name} resolution",
                    "category": "runtime",
                    "status": "WARN",
                    "detail": str(resolution.get("error") or "Runtime tool not resolved."),
                    "remediation": f"Install or register `{bundle_name}` before using that optional runtime surface.",
                }
            )
            continue
        checks.append(
            {
                "id": f"{bundle_name}-resolution",
                "label": f"{bundle_name} resolution",
                "category": "runtime",
                "status": "PASS",
                "detail": f"Resolved via {resolution.get('resolution_source')}: {resolution['target']}",
                "remediation": "",
            }
        )
        checks.append(_runtime_health_check(bundle_name, resolution))
    return checks
