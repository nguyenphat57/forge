from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


NODE_MARKERS = ("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "tsconfig.json")


def _command_check(identifier: str, label: str, command: list[str], remediation: str, *, optional: bool = False) -> dict:
    resolved = shutil.which(command[0])
    if resolved is None:
        return {
            "id": identifier,
            "label": label,
            "category": "environment",
            "status": "WARN" if optional else "FAIL",
            "detail": f"Command not found: {command[0]}",
            "remediation": remediation,
        }
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    detail = completed.stdout.strip() or completed.stderr.strip() or f"Exit code {completed.returncode}"
    return {
        "id": identifier,
        "label": label,
        "category": "environment",
        "status": "PASS" if completed.returncode == 0 else ("WARN" if optional else "FAIL"),
        "detail": detail,
        "remediation": "" if completed.returncode == 0 else remediation,
    }


def collect_environment_checks(workspace: Path) -> list[dict]:
    checks = [
        _command_check("python", "Python runtime", ["python", "--version"], "Install Python and ensure `python` is on PATH."),
        _command_check("git", "Git CLI", ["git", "--version"], "Install git and ensure `git` is on PATH."),
    ]
    node_relevant = any((workspace / marker).exists() for marker in NODE_MARKERS)
    if node_relevant:
        node_check = _command_check(
            "node",
            "Node runtime",
            ["node", "--version"],
            "Install Node.js because this workspace or runtime toolchain depends on it.",
        )
    else:
        node_check = {
            "id": "node",
            "label": "Node runtime",
            "category": "environment",
            "status": "PASS",
            "detail": "Node not required by detected workspace markers.",
            "remediation": "",
        }
    checks.append(node_check)
    return checks
