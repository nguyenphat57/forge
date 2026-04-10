from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FORGE_CORE_SCRIPTS_DIR = ROOT_DIR / "packages" / "forge-core" / "scripts"


def run_forge_core_script(script_name: str) -> None:
    target = (FORGE_CORE_SCRIPTS_DIR / script_name).resolve()
    if not target.exists():
        raise SystemExit(f"Missing forge-core script target: {target}")

    target_parent = str(target.parent)
    if target_parent not in sys.path:
        sys.path.insert(0, target_parent)

    original_argv0 = sys.argv[0]
    try:
        sys.argv[0] = str(target)
        runpy.run_path(str(target), run_name="__main__")
    finally:
        sys.argv[0] = original_argv0
