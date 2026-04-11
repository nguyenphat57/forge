from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.pop("FORGE_HOME", None)
os.environ.pop("FORGE_BUNDLE_ROOT", None)
for key in tuple(os.environ):
    if key.startswith("PYTEST_"):
        os.environ.pop(key, None)

from common import configure_stdio


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"
PREFERRED_DIST_TEST_PATTERNS = [
    "preferences_test_loading.py",
    "preferences_test_scripts.py",
    "test_adapter_locales.py",
    "test_contracts.py",
    "test_route_preview.py",
    "test_route_matrix.py",
    "test_response_contract.py",
    "test_router_matrix.py",
]


def _relative_bundle_path(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def iter_unittest_patterns() -> list[str]:
    available = {path.name for path in TESTS_DIR.glob("test_*.py")}
    available.update(path.name for path in TESTS_DIR.glob("preferences_test_*.py"))
    configured = [pattern for pattern in PREFERRED_DIST_TEST_PATTERNS if pattern in available]
    if configured:
        return configured

    return sorted(pattern for pattern in available if not pattern.endswith("_support.py"))


def _verification_env() -> dict[str, str]:
    env = os.environ.copy()
    # Dist verification must not inherit host-global Forge state from the
    # caller. Each bundle should validate against its own defaults/fixtures.
    env.pop("FORGE_HOME", None)
    env.pop("FORGE_BUNDLE_ROOT", None)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONSTARTUP", None)
    for key in tuple(env):
        if key.startswith("PYTEST_"):
            env.pop(key, None)
    return env


def _unittest_runner_command(pattern: str) -> list[str]:
    return [sys.executable, str((SCRIPTS_DIR / "verify_bundle_runner.py").resolve()), pattern]


def run_step(name: str, command: list[str]) -> dict:
    env = _verification_env()
    completed = None
    for attempt in range(5):
        completed = subprocess.run(
            command,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            env=env,
        )
        if completed.returncode != 2 or "can't open file" not in completed.stderr:
            break
        time.sleep(0.2 * (attempt + 1))
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
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run the canonical Forge bundle verification pipeline.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument(
        "--include-smoke-matrix",
        action="store_true",
        help="Also run the broader smoke matrix suites that exercise repo-level fixture packs.",
    )
    args = parser.parse_args()

    python_files = sorted(_relative_bundle_path(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(_relative_bundle_path(path) for path in TESTS_DIR.glob("*.py")))

    steps = [
        run_step("py_compile", [sys.executable, "-m", "py_compile", *python_files]),
    ]
    steps.extend(
        run_step(
            f"unittest:{pattern}",
            _unittest_runner_command(pattern),
        )
        for pattern in iter_unittest_patterns()
    )
    if args.include_smoke_matrix:
        steps.append(
            run_step(
                "smoke_matrix",
                [sys.executable, _relative_bundle_path(SCRIPTS_DIR / "run_smoke_matrix.py")],
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
