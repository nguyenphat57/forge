from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from common import configure_stdio


SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = SEMVER_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def format_version(parts: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in parts)


def bump_version(current: str, bump: str) -> str:
    major, minor, patch = parse_version(current)
    token = bump.strip().lower()
    if token == "patch":
        return format_version((major, minor, patch + 1))
    if token == "minor":
        return format_version((major, minor + 1, 0))
    if token == "major":
        return format_version((major + 1, 0, 0))
    parse_version(token)
    return token


def update_changelog_content(content: str, target_version: str) -> str:
    today = date.today().isoformat()
    heading = f"## {target_version} - {today}"
    if heading in content:
        return content

    lines = content.splitlines()
    insertion = [
        heading,
        "",
        "- Describe release changes.",
        "",
    ]
    if lines and lines[0].startswith("# "):
        new_lines = [lines[0], "", *insertion, *lines[1:]]
    else:
        new_lines = ["# Changelog", "", *insertion, *lines]
    return "\n".join(new_lines).rstrip() + "\n"


def detect_verify_command(workspace: Path) -> list[str]:
    if (workspace / "scripts" / "verify_repo.py").exists():
        return ["python", "scripts/verify_repo.py"]
    if (workspace / "scripts" / "verify_bundle.py").exists():
        return ["python", "scripts/verify_bundle.py"]
    return ["git", "diff", "--stat"]


def build_report(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    version_path = workspace / "VERSION"
    changelog_path = workspace / "CHANGELOG.md"
    if not version_path.exists():
        raise FileNotFoundError(f"Missing VERSION file: {version_path}")
    if not changelog_path.exists():
        raise FileNotFoundError(f"Missing CHANGELOG.md: {changelog_path}")

    current_version = version_path.read_text(encoding="utf-8").strip()
    parse_version(current_version)
    target_version = bump_version(current_version, args.bump)
    changelog_preview = update_changelog_content(changelog_path.read_text(encoding="utf-8"), target_version)

    changed_files = ["VERSION", "CHANGELOG.md"]
    verification_commands = [["git", "diff", "--stat"]]
    verify_command = detect_verify_command(workspace)
    if verify_command != verification_commands[0]:
        verification_commands.append(verify_command)
    if args.release_ready and verify_command not in verification_commands:
        verification_commands.append(verify_command)

    if args.apply:
        version_path.write_text(f"{target_version}\n", encoding="utf-8")
        changelog_path.write_text(changelog_preview, encoding="utf-8")

    status = "PASS"
    if target_version == current_version:
        status = "WARN"

    return {
        "status": status,
        "workspace": str(workspace),
        "current_version": current_version,
        "target_version": target_version,
        "bump": args.bump,
        "applied": args.apply,
        "changed_files": changed_files,
        "verification_commands": [" ".join(command) for command in verification_commands],
        "warnings": [] if target_version != current_version else ["Target version matches the current version."],
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Bump Preparation",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Version: {report['current_version']} -> {report['target_version']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        "- Changed files:",
    ]
    for item in report["changed_files"]:
        lines.append(f"  - {item}")
    lines.append("- Verification commands:")
    for item in report["verification_commands"]:
        lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Prepare or apply a host-neutral version bump checklist.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root containing VERSION and CHANGELOG.md")
    parser.add_argument("--bump", required=True, help="patch, minor, major, or an explicit semantic version")
    parser.add_argument("--apply", action="store_true", help="Write VERSION and CHANGELOG.md instead of previewing only")
    parser.add_argument("--release-ready", action="store_true", help="Surface the nearest release verification command")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except (FileNotFoundError, ValueError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Bump Preparation", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
