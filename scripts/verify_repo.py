from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from package_matrix import bundle_names


ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = ROOT_DIR / "packages"
DIST_DIR = ROOT_DIR / "dist"
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"
CORE_TESTS_DIR = PACKAGES_DIR / "forge-core" / "tests"


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


def _verification_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("FORGE_HOME", None)
    env.pop("FORGE_BUNDLE_ROOT", None)
    return env


def run_step(name: str, command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=_verification_env(),
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
    lines = ["Forge Repo Verify"]
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


def repo_python_files() -> list[str]:
    python_files = sorted(str(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(str(path) for path in TESTS_DIR.glob("*.py")))
    return python_files


def build_step_specs(profile: str) -> list[tuple[str, list[str], Path]]:
    step_specs: list[tuple[str, list[str], Path]] = [
        (
            "repo.generated_host_artifacts",
            [sys.executable, str(ROOT_DIR / "scripts" / "generate_host_artifacts.py"), "--check", "--format", "json"],
            ROOT_DIR,
        ),
        (
            "repo.generated_overlay_skills",
            [sys.executable, str(ROOT_DIR / "scripts" / "generate_overlay_skills.py"), "--check", "--format", "json"],
            ROOT_DIR,
        ),
        (
            "repo.py_compile",
            [sys.executable, "-m", "py_compile", *repo_python_files()],
            ROOT_DIR,
        ),
        (
            "repo.secret_scan",
            [sys.executable, str(ROOT_DIR / "scripts" / "scan_repo_secrets.py")],
            ROOT_DIR,
        ),
    ]
    if profile == "fast":
        step_specs.extend(
            [
                (
                    "repo.unittest.fast.generated_host_artifacts",
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_generated_host_artifacts.py", "-v"],
                    ROOT_DIR,
                ),
                (
                    "repo.unittest.fast.operator_surface_registry",
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_operator_surface_registry.py", "-v"],
                    ROOT_DIR,
                ),
                (
                    "repo.unittest.fast.repo_operator_shims",
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_repo_operator_script_shims.py", "-v"],
                    ROOT_DIR,
                ),
                (
                    "forge-core.unittest.fast.contracts",
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_contracts.py", "-v"],
                    PACKAGES_DIR / "forge-core",
                ),
            ]
        )
        return step_specs

    step_specs.extend(
        [
            (
                "repo.unittest",
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                ROOT_DIR,
            ),
            (
                "forge-core.verify_bundle",
                [sys.executable, str(PACKAGES_DIR / "forge-core" / "commands" / "verify_bundle.py")],
                ROOT_DIR,
            ),
            (
                "build_release",
                [sys.executable, str(ROOT_DIR / "scripts" / "build_release.py")],
                ROOT_DIR,
            ),
            (
                "install_dry_run.forge-antigravity",
                [sys.executable, str(ROOT_DIR / "scripts" / "install_bundle.py"), "forge-antigravity", "--dry-run"],
                ROOT_DIR,
            ),
            (
                "install_dry_run.forge-codex",
                [sys.executable, str(ROOT_DIR / "scripts" / "install_bundle.py"), "forge-codex", "--dry-run"],
                ROOT_DIR,
            ),
            (
                "install_dry_run.forge-codex.activate_codex",
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "install_bundle.py"),
                    "forge-codex",
                    "--dry-run",
                    "--activate-codex",
                ],
                ROOT_DIR,
            ),
            (
                "install_dry_run.forge-core",
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "install_bundle.py"),
                    "forge-core",
                    "--dry-run",
                    "--target",
                    str((Path.home() / ".forge" / "tools" / "forge-core").resolve()),
                ],
                ROOT_DIR,
            ),
        ]
    )
    for bundle_name in bundle_names():
        step_specs.append(
            (
                f"dist.{bundle_name}.verify_bundle",
                [sys.executable, str(DIST_DIR / bundle_name / "commands" / "verify_bundle.py")],
                ROOT_DIR,
            )
        )
    return step_specs


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run the canonical verification pipeline for the Forge monorepo.")
    parser.add_argument("--profile", choices=["fast", "full"], default="full", help="Verification profile")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()
    steps = [run_step(name, command, cwd) for name, command, cwd in build_step_specs(args.profile)]

    payload = {
        "status": "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL",
        "profile": args.profile,
        "steps": steps,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(steps))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
