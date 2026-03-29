from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"


def _run_step(name: str, command: list[str]) -> dict:
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
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Next.js TypeScript Postgres companion bundle.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    python_files = sorted(str(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(str(path) for path in TESTS_DIR.glob("*.py")))
    steps = [
        _run_step("py_compile", [sys.executable, "-m", "py_compile", *python_files]),
        _run_step("unittest", [sys.executable, "-m", "unittest", "discover", "-s", str(TESTS_DIR), "-v"]),
    ]
    payload = {"status": "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL", "steps": steps}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.format == "json" else json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
