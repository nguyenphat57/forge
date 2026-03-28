from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"
BROWSE_SMOKE_ENV_NAMES = ("FORGE_DESIGN_RUN_BROWSE_SMOKE", "FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE")


def run_step(name: str, command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8", check=False)
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the forge-design runtime bundle.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    python_files = sorted(str(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(str(path) for path in TESTS_DIR.glob("*.py")))
    steps = [
        run_step("py_compile", [sys.executable, "-m", "py_compile", *python_files]),
        run_step("unittest", [sys.executable, "-m", "unittest", "discover", "-s", str(TESTS_DIR), "-v"]),
    ]
    if any(os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"} for name in BROWSE_SMOKE_ENV_NAMES):
        steps.append(
            run_step(
                "design_browse_live_smoke",
                [sys.executable, str(SCRIPTS_DIR / "design_browse_live_smoke.py"), "--format", "json"],
            )
        )
    payload = {"status": "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL", "steps": steps}
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
