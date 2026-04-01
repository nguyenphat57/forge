from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"
PLAYWRIGHT_SMOKE_ENV = "FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE"
DIST_SAFE_TEST_PATTERNS = [
    "test_browse_contracts.py",
    "test_browse_packets.py",
    "test_browse_runtime.py",
    "test_browse_server.py",
    "test_browse_state.py",
    "test_playwright_cli.py",
]


def iter_unittest_patterns() -> list[str]:
    return DIST_SAFE_TEST_PATTERNS


def _relative_bundle_path(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def _verification_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("FORGE_HOME", None)
    env.pop("FORGE_BUNDLE_ROOT", None)
    env.pop("FORGE_BROWSE_STATE_ROOT", None)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONSTARTUP", None)
    env.pop("PYTEST_CURRENT_TEST", None)
    env["PYTHONPATH"] = os.pathsep.join([str(SCRIPTS_DIR), str(TESTS_DIR), str(ROOT_DIR)])
    return env


def _unittest_runner_command(pattern: str) -> list[str]:
    module_name = Path(pattern).stem
    code = (
        "import sys, unittest; "
        "from pathlib import Path; "
        "root = Path.cwd(); "
        "sys.path.insert(0, str(root / 'scripts')); "
        "sys.path.insert(0, str(root / 'tests')); "
        f"module = __import__({module_name!r}); "
        "suite = unittest.defaultTestLoader.loadTestsFromModule(module); "
        "result = unittest.TextTestRunner(verbosity=2).run(suite); "
        "raise SystemExit(0 if result.wasSuccessful() else 1)"
    )
    return [sys.executable, "-c", code]


def run_step(name: str, command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, object]:
    effective_env = dict(env or _verification_env())
    effective_cwd = cwd or ROOT_DIR
    completed = None
    for attempt in range(5):
        completed = subprocess.run(
            command,
            cwd=str(effective_cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            env=effective_env,
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


def run_isolated_test_step(pattern: str) -> dict[str, object]:
    with TemporaryDirectory() as temp_dir:
        isolated_root = Path(temp_dir) / ROOT_DIR.name
        shutil.copytree(ROOT_DIR, isolated_root)
        isolated_env = _verification_env()
        isolated_env["PYTHONPATH"] = os.pathsep.join(
            [str(isolated_root / "scripts"), str(isolated_root / "tests"), str(isolated_root)]
        )
        return run_step(
            f"unittest:{pattern}",
            _unittest_runner_command(pattern),
            cwd=isolated_root,
            env=isolated_env,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the forge-browse runtime bundle.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    python_files = sorted(_relative_bundle_path(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(_relative_bundle_path(path) for path in TESTS_DIR.glob("*.py")))
    steps = [run_step("py_compile", [sys.executable, "-m", "py_compile", *python_files])]
    steps.extend(run_isolated_test_step(pattern) for pattern in iter_unittest_patterns())
    if os.environ.get(PLAYWRIGHT_SMOKE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        steps.append(
            run_step(
                "playwright_live_smoke",
                [sys.executable, _relative_bundle_path(SCRIPTS_DIR / "playwright_live_smoke.py"), "--format", "json"],
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
