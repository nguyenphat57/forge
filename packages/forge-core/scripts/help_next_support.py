from __future__ import annotations

import json
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


def read_json_object(path: Path, label: str, warnings: list[str]) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warnings.append(f"Invalid JSON in {label}: {path}.")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{label} must contain a JSON object: {path}.")
        return None
    return payload


def first_existing_file(workspace: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = workspace / name
        if candidate.exists():
            return candidate
    return None


def _markdown_rank(path: Path) -> tuple[float, str]:
    try:
        return path.stat().st_mtime, str(path).lower()
    except OSError:
        return float("-inf"), ""


def find_latest_markdown(workspace: Path, relative_dir: str) -> Path | None:
    base_dir = workspace / relative_dir
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob("*.md"):
        rank = _markdown_rank(candidate)
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def extract_markdown_title(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title.lower().startswith("plan:"):
                return title.split(":", 1)[1].strip()
            if title.lower().startswith("spec:"):
                return title.split(":", 1)[1].strip()
            return title
    return path.stem


def read_handover_excerpt(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.upper() == "HANDOVER":
            continue
        return stripped[2:].strip() if stripped.startswith("- ") else stripped
    return None


def read_git_status(workspace: Path) -> dict:
    empty = {"available": False, "changed_files": [], "untracked_files": []}
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all", "--", "."],
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
    for line in completed.stdout.splitlines():
        entry = line.rstrip()
        if len(entry) < 4:
            continue
        path = entry[3:].strip().split(" -> ", 1)[-1]
        if entry[:2] == "??":
            untracked_files.append(path)
        else:
            changed_files.append(path)
    return {"available": True, "changed_files": changed_files, "untracked_files": untracked_files}


def session_task(session: dict | None) -> str | None:
    if not session:
        return None
    working_on = session.get("working_on")
    if isinstance(working_on, dict):
        for key in ("task", "feature"):
            value = working_on.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def session_blocker(session: dict | None) -> str | None:
    if not session:
        return None
    for key in ("blocker", "blockers"):
        value = session.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return None


def pending_tasks(session: dict | None) -> list[str]:
    if not session:
        return []
    values = session.get("pending_tasks")
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


def determine_stage(*, session: dict | None, git_state: dict, latest_plan: Path | None, latest_spec: Path | None) -> str:
    working_on = session.get("working_on") if isinstance(session, dict) else None
    if isinstance(working_on, dict):
        status = working_on.get("status")
        if isinstance(status, str) and status.strip().lower() == "blocked":
            return "blocked"
    if session_blocker(session):
        return "blocked"
    if session_task(session) or pending_tasks(session):
        return "session-active"
    if git_state["changed_files"] or git_state["untracked_files"]:
        return "active-changes"
    if latest_plan or latest_spec:
        return "planned"
    return "unscoped"


def build_focus(stage: str, *, session: dict | None, latest_plan: Path | None, latest_spec: Path | None, git_state: dict) -> str:
    if stage == "blocked":
        return f"Blocked: {session_blocker(session)}"
    if stage == "session-active":
        return f"Session task: {session_task(session) or pending_tasks(session)[0]}"
    if stage == "active-changes":
        total = len(git_state["changed_files"]) + len(git_state["untracked_files"])
        return f"Working tree has {total} changed file(s)."
    if stage == "planned":
        return f"Plan: {extract_markdown_title(latest_plan)}" if latest_plan is not None else f"Spec: {extract_markdown_title(latest_spec)}"
    return "No active slice detected from repo state."


def build_recommendations(
    *,
    mode: str,
    stage: str,
    session: dict | None,
    latest_plan: Path | None,
    latest_spec: Path | None,
    handover_excerpt: str | None,
) -> tuple[str, str, list[str]]:
    plan_path = latest_plan or latest_spec
    plan_kind = "plan" if latest_plan is not None else "spec"
    plan_title = extract_markdown_title(plan_path)
    pending = pending_tasks(session)
    if stage == "blocked":
        blocker = session_blocker(session) or handover_excerpt or "Validate the current blocker."
        alternatives = []
        if plan_title:
            alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' to confirm the intended recovery path.")
        alternatives.append("If the blocker keeps drifting, capture a fresh handover with the missing evidence.")
        return "debug", f"Resolve the blocker first: {blocker}.", alternatives[:2]
    if stage == "session-active":
        primary = f"Resume the highest-signal pending task: {pending[0]}." if pending else f"Continue the active task: {session_task(session)}."
        alternatives: list[str] = []
        if len(pending) > 1:
            alternatives.append(f"Continue secondary pending task: {pending[1]}.")
        if plan_title:
            alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' if priorities changed.")
        return "session", primary, alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "active-changes":
        alternatives = []
        if plan_title:
            alternatives.append(f"Update the latest {plan_kind} '{plan_title}' if the current diff drifted from the intended slice.")
        alternatives.append("If the slice is already complete, run a review pass and decide whether to merge or continue.")
        return "review", "Review the current changed files and run the nearest verification before adding new edits.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "planned":
        label = plan_title or "the latest plan"
        alternatives = [
            "If scope is still fuzzy, tighten the plan before writing code.",
            "If repo health is unclear, run a review-style scan before implementation.",
        ]
        return "plan", f"Start the first concrete slice from {plan_kind} '{label}'.", alternatives[:1] if mode == "next" else alternatives[:2]
    alternatives = [
        "If you already know the task, state it directly and let Forge route the right workflow.",
        "If the repo feels unhealthy, run a review-style scan before new implementation.",
    ]
    return "review", "Start from README, package manifests, and docs/plans to identify the active workflow.", alternatives[:1] if mode == "next" else alternatives[:2]


def build_evidence(
    *,
    readme: Path | None,
    latest_plan: Path | None,
    latest_spec: Path | None,
    session_path: Path | None,
    handover_path: Path | None,
    git_state: dict,
    preferences_source: dict,
) -> list[str]:
    evidence: list[str] = []
    if readme is not None:
        evidence.append(f"readme: {readme}")
    if latest_plan is not None:
        evidence.append(f"plan: {latest_plan}")
    if latest_spec is not None:
        evidence.append(f"spec: {latest_spec}")
    if session_path is not None and session_path.exists():
        evidence.append(f"session: {session_path}")
    if handover_path is not None and handover_path.exists():
        evidence.append(f"handover: {handover_path}")
    if git_state["changed_files"] or git_state["untracked_files"]:
        count = len(git_state["changed_files"]) + len(git_state["untracked_files"])
        evidence.append(f"git: {count} working tree item(s)")
    if preferences_source["path"]:
        evidence.append(f"preferences: {preferences_source['path']}")
    return evidence
