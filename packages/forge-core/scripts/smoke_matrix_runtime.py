from __future__ import annotations

import os
import subprocess
from pathlib import Path

from smoke_matrix_cases import FORGE_HOMES_DIR, ROOT_DIR, RUN_HELPERS_DIR


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env.setdefault("FORGE_HOME", str(FORGE_HOMES_DIR / "empty"))
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=merged_env,
    )


def resolve_run_command(parts: list[str]) -> list[str]:
    resolved: list[str] = []
    for part in parts:
        candidate = RUN_HELPERS_DIR / part
        if part.endswith(".py") and candidate.exists():
            resolved.append(str(candidate))
        else:
            resolved.append(part)
    return resolved


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
