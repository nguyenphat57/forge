from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

from package_matrix import bundle_names


ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = ROOT_DIR / "packages"
DIST_DIR = ROOT_DIR / "dist"
SCRIPTS_DIR = ROOT_DIR / "scripts"
TESTS_DIR = ROOT_DIR / "tests"


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() != "utf-8":
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8"))


def run_step(name: str, command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
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


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Run the canonical verification pipeline for the Forge monorepo.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    python_files = sorted(str(path) for path in SCRIPTS_DIR.glob("*.py"))
    python_files.extend(sorted(str(path) for path in TESTS_DIR.glob("*.py")))

    steps = [
        run_step(
            "repo.generated_host_artifacts",
            [sys.executable, str(ROOT_DIR / "scripts" / "generate_host_artifacts.py"), "--check", "--format", "json"],
            ROOT_DIR,
        ),
        run_step(
            "repo.py_compile",
            [sys.executable, "-m", "py_compile", *python_files],
            ROOT_DIR,
        ),
        run_step(
            "repo.secret_scan",
            [sys.executable, str(ROOT_DIR / "scripts" / "scan_repo_secrets.py")],
            ROOT_DIR,
        ),
        run_step(
            "repo.unittest",
            [sys.executable, "-m", "unittest", "discover", "-s", str(TESTS_DIR), "-v"],
            ROOT_DIR,
        ),
        run_step(
            "forge-core.verify_bundle",
            [sys.executable, str(PACKAGES_DIR / "forge-core" / "scripts" / "verify_bundle.py")],
            ROOT_DIR,
        ),
        run_step(
            "build_release",
            [sys.executable, str(ROOT_DIR / "scripts" / "build_release.py")],
            ROOT_DIR,
        ),
        run_step(
            "install_dry_run.forge-antigravity",
            [sys.executable, str(ROOT_DIR / "scripts" / "install_bundle.py"), "forge-antigravity", "--dry-run"],
            ROOT_DIR,
        ),
        run_step(
            "install_dry_run.forge-codex",
            [sys.executable, str(ROOT_DIR / "scripts" / "install_bundle.py"), "forge-codex", "--dry-run"],
            ROOT_DIR,
        ),
        run_step(
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
        run_step(
            "install_dry_run.forge-browse",
            [
                sys.executable,
                str(ROOT_DIR / "scripts" / "install_bundle.py"),
                "forge-browse",
                "--dry-run",
                "--target",
                str((Path.home() / ".forge" / "tools" / "forge-browse").resolve()),
            ],
            ROOT_DIR,
        ),
        run_step(
            "install_dry_run.forge-design",
            [
                sys.executable,
                str(ROOT_DIR / "scripts" / "install_bundle.py"),
                "forge-design",
                "--dry-run",
                "--target",
                str((Path.home() / ".forge" / "tools" / "forge-design").resolve()),
            ],
            ROOT_DIR,
        ),
        run_step(
            "install_dry_run.forge-nextjs-typescript-postgres",
            [
                sys.executable,
                str(ROOT_DIR / "scripts" / "install_bundle.py"),
                "forge-nextjs-typescript-postgres",
                "--dry-run",
                "--target",
                str((Path.home() / ".forge" / "companions" / "forge-nextjs-typescript-postgres").resolve()),
            ],
            ROOT_DIR,
        ),
    ]

    for bundle_name in bundle_names():
        steps.append(
            run_step(
                f"dist.{bundle_name}.verify_bundle",
                [sys.executable, str(DIST_DIR / bundle_name / "scripts" / "verify_bundle.py")],
                ROOT_DIR,
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
