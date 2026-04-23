from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from operator_state_resolution import (
    build_evidence,
    build_focus,
    build_recommendations,
    determine_stage,
    effective_workflow_summary,
    filter_stale_session_items,
    filtered_pending_tasks,
    git_handoff_clean,
    git_worktree_clean,
    pending_tasks,
    session_blocker,
    session_status_value,
    session_task,
    workflow_state_follow_on_stages,
    workflow_state_has_actionable_slice,
    workflow_state_has_recorded_slice,
    workflow_state_required_chain,
    workflow_state_stage,
    workflow_summary_is_stale_merge_handoff,
)


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


def read_json_object(path: Path, label: str, warnings: list[str]) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warnings.append(f"Invalid JSON in {label}: {path}.")
        return None
    return payload if isinstance(payload, dict) else None


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


def find_latest_named_file(workspace: Path, relative_dir: str, filename: str) -> Path | None:
    return find_latest_file(workspace, relative_dir, filename)


def find_latest_json(workspace: Path, relative_dir: str) -> Path | None:
    return find_latest_file(workspace, relative_dir, "*.json")


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
    branch = {
        "branch_head": None,
        "branch_upstream": None,
        "ahead": None,
        "behind": None,
        "synced_with_upstream": None,
    }
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

    head = match.group("head")
    upstream = match.group("upstream")
    ab = match.group("ab") or ""
    ahead = 0
    behind = 0
    for part in (item.strip() for item in ab.split(",") if item.strip()):
        if part.startswith("ahead "):
            try:
                ahead = int(part.removeprefix("ahead ").strip())
            except ValueError:
                ahead = 0
        elif part.startswith("behind "):
            try:
                behind = int(part.removeprefix("behind ").strip())
            except ValueError:
                behind = 0

    branch["branch_head"] = head.strip() or None
    branch["branch_upstream"] = upstream.strip() if isinstance(upstream, str) and upstream.strip() else None
    if branch["branch_upstream"]:
        branch["ahead"] = ahead
        branch["behind"] = behind
        branch["synced_with_upstream"] = ahead == 0 and behind == 0
    return branch


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
        if (
            relative.startswith(".forge-artifacts/")
            or relative.startswith(".forge-artifacts\\")
            or relative.startswith(".brain/")
            or relative.startswith(".brain\\")
        ):
            continue
        if line[:2] == "??":
            untracked_files.append(relative)
        else:
            changed_files.append(relative)
    return {
        "available": True,
        "changed_files": changed_files,
        "untracked_files": untracked_files,
        "branch_head": branch["branch_head"],
        "branch_upstream": branch["branch_upstream"],
        "ahead": branch["ahead"],
        "behind": branch["behind"],
        "synced_with_upstream": branch["synced_with_upstream"],
    }
