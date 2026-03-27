from __future__ import annotations

import re
from datetime import date
from pathlib import Path


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
