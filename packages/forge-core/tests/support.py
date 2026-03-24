from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
WORKSPACES_DIR = FIXTURES_DIR / "workspaces"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def build_route_args(
    prompt: str,
    *,
    repo_signals: list[str] | None = None,
    workspace_router: Path | None = None,
    changed_files: int | None = None,
    has_harness: str = "auto",
) -> Namespace:
    return Namespace(
        prompt=prompt,
        repo_signal=repo_signals or [],
        workspace_router=workspace_router,
        changed_files=changed_files,
        has_harness=has_harness,
        format="json",
        persist=False,
        output_dir=None,
    )


def load_json_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def workspace_fixture(name: str) -> Path:
    return WORKSPACES_DIR / name


def run_python_script(script_name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPTS_DIR / script_name), *args]
    return subprocess.run(
        command,
        cwd=str(cwd or ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
