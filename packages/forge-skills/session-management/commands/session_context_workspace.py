from __future__ import annotations

import re
import subprocess
from pathlib import Path


MARKER_FILES = ("README.md", "README", "package.json", "pyproject.toml", "go.mod", "pom.xml", "build.gradle", "Cargo.toml")
MARKER_DIRS = ("docs", "src", "app", "tests")


def collect_repo_signals(workspace: Path) -> list[str]:
    signals: list[str] = []
    for marker in MARKER_FILES:
        if (workspace / marker).exists():
            signals.append(marker)
    for marker in MARKER_DIRS:
        if (workspace / marker).exists():
            signals.append(marker)
    return signals


def first_existing_file(workspace: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = workspace / name
        if candidate.exists():
            return candidate
    return None


def _mtime_rank(path: Path) -> tuple[float, str]:
    try:
        return path.stat().st_mtime, str(path).lower()
    except OSError:
        return float("-inf"), ""


def find_latest_file(workspace: Path, relative_dir: str, pattern: str) -> Path | None:
    base_dir = workspace / relative_dir
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob(pattern):
        rank = _mtime_rank(candidate)
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def find_latest_markdown(workspace: Path, relative_dir: str) -> Path | None:
    return find_latest_file(workspace, relative_dir, "*.md")


def extract_markdown_title(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if ":" in title and title.split(":", 1)[0].lower() in {"plan", "spec"}:
                return title.split(":", 1)[1].strip()
            return title
    return path.stem


def read_handover_excerpt(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and stripped.upper() != "HANDOVER":
            return stripped[2:].strip() if stripped.startswith("- ") else stripped
    return None


def _parse_git_branch_status(line: str) -> dict[str, object]:
    branch = {"branch_head": None, "branch_upstream": None, "ahead": None, "behind": None, "synced_with_upstream": None}
    if not line.startswith("## "):
        return branch
    content = line[3:].strip()
    if not content:
        return branch
    if content.startswith("No commits yet on "):
        branch["branch_head"] = content.removeprefix("No commits yet on ").strip() or None
        return branch
    if content == "HEAD (no branch)":
        branch["branch_head"] = "HEAD"
        return branch
    match = re.match(r"^(?P<head>.+?)(?:\.\.\.(?P<upstream>[^\[]+?))?(?: \[(?P<ab>[^\]]+)\])?$", content)
    if not match:
        branch["branch_head"] = content
        return branch
    branch["branch_head"] = match.group("head").strip() or None
    upstream = match.group("upstream")
    if isinstance(upstream, str) and upstream.strip():
        branch["branch_upstream"] = upstream.strip()
        ahead, behind = _parse_ahead_behind(match.group("ab") or "")
        branch["ahead"] = ahead
        branch["behind"] = behind
        branch["synced_with_upstream"] = ahead == 0 and behind == 0
    return branch


def _parse_ahead_behind(text: str) -> tuple[int, int]:
    ahead = 0
    behind = 0
    for part in (item.strip() for item in text.split(",") if item.strip()):
        try:
            if part.startswith("ahead "):
                ahead = int(part.removeprefix("ahead ").strip())
            elif part.startswith("behind "):
                behind = int(part.removeprefix("behind ").strip())
        except ValueError:
            continue
    return ahead, behind


def read_git_status(workspace: Path) -> dict:
    empty = {
        "available": False,
        "changed_files": [],
        "untracked_files": [],
        "branch_head": None,
        "branch_upstream": None,
        "ahead": None,
        "behind": None,
        "synced_with_upstream": None,
    }
    completed = subprocess.run(
        ["git", "status", "--short", "--branch", "--untracked-files=all", "--", "."],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return empty
    changed_files: list[str] = []
    untracked_files: list[str] = []
    branch = empty.copy()
    for line in completed.stdout.splitlines():
        if line.startswith("## "):
            branch = {**branch, **_parse_git_branch_status(line)}
            continue
        if len(line) < 4:
            continue
        relative = line[3:].strip().split(" -> ", 1)[-1]
        if relative.startswith((".forge-artifacts/", ".forge-artifacts\\", ".brain/", ".brain\\")):
            continue
        if line[:2] == "??":
            untracked_files.append(relative)
        else:
            changed_files.append(relative)
    return {
        **branch,
        "available": True,
        "changed_files": changed_files,
        "untracked_files": untracked_files,
    }
