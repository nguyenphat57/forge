from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _script_path(match: dict, capability_key: str) -> Path | None:
    capability = match["spec"]["capabilities"].get(capability_key)
    if not isinstance(capability, dict):
        return None
    script = capability.get("script")
    if not isinstance(script, str) or not script.strip():
        return None
    return Path(match["spec"]["package_dir"]) / script


def invoke_companion_capability(match: dict, capability_key: str, workspace: Path, extra_args: list[str] | None = None) -> dict | None:
    script_path = _script_path(match, capability_key)
    if script_path is None or not script_path.exists():
        return None
    completed = subprocess.run(
        [sys.executable, str(script_path), "--workspace", str(workspace), "--format", "json", *(extra_args or [])],
        cwd=str(match["spec"]["package_dir"]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0 and not completed.stdout.strip():
        raise RuntimeError(completed.stderr.strip() or f"Companion capability failed: {script_path}")
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def invoke_companion_preset(preset_match: dict, workspace: Path, project_name: str | None, apply: bool) -> dict:
    script_rel = preset_match["preset"].get("script")
    if not isinstance(script_rel, str) or not script_rel.strip():
        raise ValueError(f"Preset '{preset_match['full_id']}' does not declare a scaffold script.")
    script_path = Path(preset_match["spec"]["package_dir"]) / script_rel
    command = [sys.executable, str(script_path), "--workspace", str(workspace), "--preset", str(preset_match["preset"]["id"]), "--format", "json"]
    if project_name:
        command.extend(["--project-name", project_name])
    if apply:
        command.append("--apply")
    completed = subprocess.run(
        command,
        cwd=str(preset_match["spec"]["package_dir"]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"Preset failed: {preset_match['full_id']}")
    return json.loads(completed.stdout)
