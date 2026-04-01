from __future__ import annotations

import json
import subprocess
from pathlib import Path

from workflow_state_summary import summary_items, summary_text, workflow_summary


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
        if len(line) < 4:
            continue
        relative = line[3:].strip().split(" -> ", 1)[-1]
        if relative.startswith(".forge-artifacts/") or relative.startswith(".forge-artifacts\\"):
            continue
        if line[:2] == "??":
            untracked_files.append(relative)
        else:
            changed_files.append(relative)
    return {"available": True, "changed_files": changed_files, "untracked_files": untracked_files}


def session_task(session: dict | None) -> str | None:
    if not isinstance(session, dict):
        return None
    working_on = session.get("working_on")
    if isinstance(working_on, dict):
        for key in ("task", "feature"):
            value = working_on.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def session_blocker(session: dict | None) -> str | None:
    if not isinstance(session, dict):
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
    if not isinstance(session, dict):
        return []
    values = session.get("pending_tasks")
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


def workflow_state_stage(workflow_state: dict | None) -> str | None:
    if not isinstance(workflow_state, dict):
        return None
    current_stage = workflow_state.get("current_stage")
    return current_stage.strip() if isinstance(current_stage, str) and current_stage.strip() else None


def workflow_state_required_chain(workflow_state: dict | None) -> list[str]:
    if not isinstance(workflow_state, dict):
        return []
    required_stage_chain = workflow_state.get("required_stage_chain")
    if not isinstance(required_stage_chain, list):
        return []
    return [item.strip() for item in required_stage_chain if isinstance(item, str) and item.strip()]


def workflow_state_has_recorded_slice(workflow_state: dict | None) -> bool:
    if not isinstance(workflow_state, dict):
        return False
    if workflow_state_stage(workflow_state):
        return True
    if workflow_state_required_chain(workflow_state):
        return True
    stages = workflow_state.get("stages")
    return isinstance(stages, dict) and bool(stages)


def workflow_state_follow_on_stages(workflow_state: dict | None) -> list[str]:
    current_stage = workflow_state_stage(workflow_state)
    required_stage_chain = workflow_state_required_chain(workflow_state)
    if current_stage and current_stage in required_stage_chain:
        return required_stage_chain[required_stage_chain.index(current_stage) + 1 :]
    return required_stage_chain


def release_tier_label(release_readiness: dict | None) -> str | None:
    if not isinstance(release_readiness, dict):
        return None
    tier = release_readiness.get("release_tier")
    return tier.strip() if isinstance(tier, str) and tier.strip() else None


def adoption_signal_label(latest_adoption_check: dict | None) -> str | None:
    if not isinstance(latest_adoption_check, dict):
        return None
    impact = latest_adoption_check.get("impact")
    confidence = latest_adoption_check.get("confidence")
    summary = latest_adoption_check.get("summary") or latest_adoption_check.get("label")
    parts = [item for item in (impact, confidence) if isinstance(item, str) and item.strip()]
    if not parts and not isinstance(summary, str):
        return None
    prefix = " / ".join(parts)
    if isinstance(summary, str) and summary.strip():
        return f"{prefix}: {summary.strip()}" if prefix else summary.strip()
    return prefix or None


def determine_stage(*, session: dict | None, git_state: dict, latest_plan: Path | None, latest_spec: Path | None, workflow_state: dict | None = None, codebase_summary: Path | None = None, active_change: dict | None = None) -> str:
    summary = workflow_summary(workflow_state)
    status = summary_text(summary, "status")
    if status == "blocked":
        return "blocked"
    if status == "review-ready":
        return "review-ready"
    if status == "active":
        if summary_text(summary, "primary_kind") == "route-preview":
            return "change-active"
        return "session-active"
    working_on = session.get("working_on") if isinstance(session, dict) else None
    if isinstance(working_on, dict) and isinstance(working_on.get("status"), str) and working_on["status"].strip().lower() == "blocked":
        return "blocked"
    if session_blocker(session):
        return "blocked"
    if session_task(session) or pending_tasks(session):
        return "session-active"
    if isinstance(active_change, dict) and str(active_change.get("state") or "").lower() not in {"archived", "done", "closed"}:
        return "change-active"
    if workflow_state_has_recorded_slice(workflow_state):
        return "change-active"
    if git_state["changed_files"] or git_state["untracked_files"]:
        return "active-changes"
    if latest_plan or latest_spec:
        return "planned"
    if codebase_summary is not None:
        return "mapped"
    return "unscoped"


def build_focus(
    stage: str,
    *,
    session: dict | None,
    latest_plan: Path | None,
    latest_spec: Path | None,
    git_state: dict,
    workflow_state: dict | None = None,
    codebase_summary: Path | None = None,
    active_change: dict | None = None,
    release_readiness: dict | None = None,
    latest_adoption_check: dict | None = None,
) -> str:
    summary = workflow_summary(workflow_state)
    workflow_focus = summary_text(summary, "current_focus")
    workflow_stage = workflow_state_stage(workflow_state)
    release_tier = release_tier_label(release_readiness)
    release_signal = adoption_signal_label(latest_adoption_check)
    if workflow_stage in {"release-doc-sync", "release-readiness", "adoption-check"}:
        label = f"Release tail: {workflow_stage}"
        if release_tier:
            label = f"{label} ({release_tier})"
        if workflow_stage == "adoption-check" and release_signal:
            return f"{label} | {release_signal}"
        return label
    if stage == "blocked":
        return workflow_focus or f"Blocked: {session_blocker(session)}"
    if stage == "review-ready":
        return workflow_focus or "Work slice is ready for review."
    if stage == "session-active":
        return workflow_focus or f"Session task: {session_task(session) or pending_tasks(session)[0]}"
    if stage == "change-active":
        if workflow_focus:
            return workflow_focus
        if workflow_stage:
            return f"Recorded workflow stage: {workflow_stage}"
        return "Active change: {0} ({1})".format(
            active_change.get("summary", active_change.get("slug", "change")),
            active_change.get("state", "active"),
        )
    if stage == "active-changes":
        total = len(git_state["changed_files"]) + len(git_state["untracked_files"])
        return f"Working tree contains {total} changed file(s)."
    if stage == "planned":
        return f"Plan: {extract_markdown_title(latest_plan)}" if latest_plan is not None else f"Spec: {extract_markdown_title(latest_spec)}"
    if stage == "mapped":
        return f"Codebase map: {codebase_summary}" if codebase_summary is not None else "Mapped repo summary available."
    return "No active work slice detected from repo state."


def build_recommendations(
    *,
    mode: str,
    stage: str,
    session: dict | None,
    latest_plan: Path | None,
    latest_spec: Path | None,
    handover_excerpt: str | None,
    workflow_state: dict | None = None,
    codebase_summary: Path | None = None,
    active_change: dict | None = None,
    release_readiness: dict | None = None,
    latest_adoption_check: dict | None = None,
) -> tuple[str, str, list[str]]:
    summary = workflow_summary(workflow_state)
    workflow_name = summary_text(summary, "suggested_workflow")
    workflow_action = summary_text(summary, "recommended_action")
    workflow_alternatives = summary_items(summary, "alternatives")
    workflow_stage = workflow_state_stage(workflow_state)
    workflow_follow_on = workflow_state_follow_on_stages(workflow_state)
    release_tier = release_tier_label(release_readiness)
    release_signal = adoption_signal_label(latest_adoption_check)
    if summary and stage in {"blocked", "review-ready", "session-active"} and workflow_name and workflow_action:
        return workflow_name, workflow_action, workflow_alternatives[:1] if mode == "next" else workflow_alternatives[:2]
    plan_path = latest_plan or latest_spec
    plan_kind = "plan" if latest_plan is not None else "spec"
    plan_title = extract_markdown_title(plan_path)
    pending = pending_tasks(session)
    if stage == "blocked":
        blocker = session_blocker(session) or handover_excerpt or "Validate the current blocker."
        alternatives = [f"Re-open the latest {plan_kind} '{plan_title}' to confirm the intended recovery path."] if plan_title else []
        alternatives.append("If the blocker keeps drifting, capture a fresh handover with the missing evidence.")
        return "debug", f"Resolve the blocker first: {blocker}.", alternatives[:2]
    if stage == "session-active":
        primary = f"Resume the highest-priority pending task: {pending[0]}." if pending else f"Continue the active task: {session_task(session)}."
        alternatives: list[str] = []
        if len(pending) > 1:
            alternatives.append(f"Continue secondary pending task: {pending[1]}.")
        if plan_title:
            alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' if priorities changed.")
        return "session", primary, alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "change-active":
        if workflow_stage in {"release-doc-sync", "release-readiness", "adoption-check"}:
            alternatives = list(workflow_alternatives)
            if release_signal:
                alternatives.append(f"Keep the latest adoption signal visible: {release_signal}.")
            if release_tier:
                alternatives.append(f"Release tier in effect: {release_tier}.")
            action = workflow_action or f"Continue the recorded release tail at '{workflow_stage}'."
            if release_tier and release_tier not in action:
                action = f"{action} Release tier: {release_tier}."
            if workflow_stage == "adoption-check" and latest_adoption_check:
                impact = latest_adoption_check.get("impact")
                if isinstance(impact, str) and impact in {"neutral", "contradicts"}:
                    action = f"{action} Feed the signal back into release-readiness before opening new scope."
            return workflow_name or workflow_stage, action, alternatives[:1] if mode == "next" else alternatives[:2]
        if workflow_name and workflow_action:
            return workflow_name, workflow_action, workflow_alternatives[:1] if mode == "next" else workflow_alternatives[:2]
        if workflow_stage:
            alternatives: list[str] = []
            if workflow_follow_on:
                alternatives.append(f"After '{workflow_stage}', continue into '{workflow_follow_on[0]}'.")
            if plan_title:
                alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' if the recorded stage no longer matches the intended slice.")
            return workflow_stage, f"Resume the recorded workflow stage '{workflow_stage}' before opening new scope.", alternatives[:1] if mode == "next" else alternatives[:2]
        summary = active_change.get("summary", active_change.get("slug", "change")) if isinstance(active_change, dict) else "active change"
        state = active_change.get("state", "active") if isinstance(active_change, dict) else "active"
        alternatives = ["Update the change status before new edits if reality drifted.", "Archive the change if the slice is already complete."]
        return "session", f"Resume the active change '{summary}' from state '{state}'.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "review-ready":
        alternatives = [f"Re-open the latest {plan_kind} '{plan_title}' if the review uncovered scope drift."] if plan_title else []
        alternatives.append("If review passes cleanly, advance to the next recorded stage instead of opening new scope.")
        return "review", "Run review and the nearest verification pass before resuming implementation.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "active-changes":
        alternatives = [f"Update the latest {plan_kind} '{plan_title}' if the current diff drifted from the intended slice."] if plan_title else []
        alternatives.append("If the slice is already complete, run a review pass and decide whether to merge or continue.")
        return "review", "Review the current changed files and run the nearest verification before adding new edits.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "planned":
        label = plan_title or "the latest plan"
        alternatives = ["If scope is still fuzzy, tighten the plan before writing code.", "If repo health is unclear, run a review-style scan before implementation."]
        return "plan", f"Start the first concrete slice from {plan_kind} '{label}'.", alternatives[:1] if mode == "next" else alternatives[:2]
    if stage == "mapped":
        alternatives = ["Refresh the codebase map if the repo changed materially.", "Use `review` only after a concrete slice is already active or review-ready."]
        return "plan", "Use the brownfield codebase map to choose the first concrete slice, then record a plan or change artifact before editing.", alternatives[:1] if mode == "next" else alternatives[:2]
    alternatives = ["If Forge wiring feels broken, run `doctor` first to confirm runtime and workspace health.", "If you already know the task, state it directly and let Forge route the right workflow after the repo is mapped."]
    return "map-codebase", "Run `doctor` and `map-codebase` to establish repo health and a durable brownfield summary before editing.", alternatives[:1] if mode == "next" else alternatives[:2]


def build_evidence(*, readme: Path | None, latest_plan: Path | None, latest_spec: Path | None, session_path: Path | None, handover_path: Path | None, git_state: dict, preferences_source: dict, workflow_source: dict, codebase_summary: Path | None = None) -> list[str]:
    evidence: list[str] = []
    if readme is not None:
        evidence.append(f"readme: {readme}")
    if codebase_summary is not None:
        evidence.append(f"codebase-summary: {codebase_summary}")
    if latest_plan is not None:
        evidence.append(f"plan: {latest_plan}")
    if latest_spec is not None:
        evidence.append(f"spec: {latest_spec}")
    if session_path is not None and session_path.exists():
        evidence.append(f"session: {session_path}")
    if handover_path is not None and handover_path.exists():
        evidence.append(f"handover: {handover_path}")
    if git_state["changed_files"] or git_state["untracked_files"]:
        evidence.append(f"git: {len(git_state['changed_files']) + len(git_state['untracked_files'])} working tree item(s)")
    if preferences_source["path"]:
        evidence.append(f"preferences: {preferences_source['path']}")
    if workflow_source.get("path"):
        evidence.append(f"workflow-state: {workflow_source['path']}")
    return evidence
