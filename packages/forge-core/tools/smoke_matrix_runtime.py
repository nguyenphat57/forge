from __future__ import annotations

import os
import subprocess

from smoke_matrix_cases import FORGE_HOMES_DIR, ROOT_DIR


def _smoke_matrix_env(env: dict[str, str] | None = None) -> dict[str, str]:
    merged_env = os.environ.copy()
    # Ignore inherited host state so smoke cases stay deterministic even when
    # the parent process points FORGE_HOME at an installed bundle/runtime.
    merged_env.pop("FORGE_HOME", None)
    merged_env.pop("FORGE_BUNDLE_ROOT", None)
    merged_env.pop("PYTHONPATH", None)
    merged_env.pop("PYTHONHOME", None)
    merged_env.pop("PYTHONSTARTUP", None)
    for key in tuple(merged_env):
        if key.startswith("PYTEST_"):
            merged_env.pop(key, None)
    merged_env["FORGE_HOME"] = str(FORGE_HOMES_DIR / "empty")
    if env:
        merged_env.update(env)
    return merged_env


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=_smoke_matrix_env(env),
    )


def case_failure(suite: str, name: str, message: str, output: str) -> dict:
    failures = [message]
    cleaned_output = output.strip()
    if cleaned_output:
        failures.append(cleaned_output)
    return {
        "suite": suite,
        "name": name,
        "status": "FAIL",
        "failures": failures,
    }


def case_result(suite: str, name: str, failures: list[str]) -> dict:
    return {
        "suite": suite,
        "name": name,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }


def summarize(results: list[dict]) -> dict:
    passes = sum(1 for item in results if item["status"] == "PASS")
    failures = [item for item in results if item["status"] == "FAIL"]
    return {
        "total": len(results),
        "passed": passes,
        "failed": len(failures),
        "failures": failures,
    }


def format_text(summary: dict, results: list[dict]) -> str:
    lines = [
        "Forge Smoke Matrix",
        f"- Total: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "- Results:",
    ]
    for item in results:
        lines.append(f"  - [{item['status']}] {item['suite']} :: {item['name']}")
        for failure in item["failures"]:
            lines.append(f"    - {failure}")
    return "\n".join(lines)
