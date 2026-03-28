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
PLAYWRIGHT_SMOKE_ENV = "FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE"


def run_step(name: str, command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the forge-browse runtime bundle.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    python_files = sorted(str(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(str(path) for path in TESTS_DIR.glob("*.py")))
    steps = [
        run_step("py_compile", [sys.executable, "-m", "py_compile", *python_files]),
        run_step("unittest", [sys.executable, "-m", "unittest", "discover", "-s", str(TESTS_DIR), "-v"]),
    ]
    if os.environ.get(PLAYWRIGHT_SMOKE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        steps.append(
            run_step(
                "playwright_live_smoke",
                [sys.executable, str(SCRIPTS_DIR / "playwright_live_smoke.py"), "--format", "json"],
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
