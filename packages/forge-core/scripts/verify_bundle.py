from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"


def run_step(name: str, command: list[str]) -> dict:
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


def format_text(steps: list[dict]) -> str:
    lines = ["Forge Bundle Verify"]
    for step in steps:
        lines.append(f"- [{step['status']}] {step['name']}")
        lines.append(f"  Command: {' '.join(step['command'])}")
        if step["stdout"]:
            lines.append("  Stdout:")
            for line in step["stdout"].splitlines():
                lines.append(f"    {line}")
        if step["stderr"]:
            lines.append("  Stderr:")
            for line in step["stderr"].splitlines():
                lines.append(f"    {line}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical Forge bundle verification pipeline.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--include-canary", action="store_true", help="Also evaluate persisted canary readiness.")
    parser.add_argument(
        "--canary-dir",
        default=str(ROOT_DIR / ".forge-artifacts" / "canary-runs"),
        help="Directory containing canary artifacts for readiness evaluation",
    )
    parser.add_argument(
        "--canary-profile",
        choices=["controlled-rollout", "broad"],
        default="controlled-rollout",
        help="Canary readiness threshold profile",
    )
    args = parser.parse_args()

    python_files = sorted(str(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(str(path) for path in TESTS_DIR.glob("*.py")))

    steps = [
        run_step("py_compile", [sys.executable, "-m", "py_compile", *python_files]),
        run_step("unittest", [sys.executable, "-m", "unittest", "discover", "-s", str(TESTS_DIR), "-v"]),
        run_step("smoke_matrix", [sys.executable, str(SCRIPTS_DIR / "run_smoke_matrix.py")]),
    ]
    if args.include_canary:
        steps.append(
            run_step(
                "canary_readiness",
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "evaluate_canary_readiness.py"),
                    args.canary_dir,
                    "--profile",
                    args.canary_profile,
                ],
            )
        )

    payload = {
        "status": "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL",
        "steps": steps,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(steps))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
