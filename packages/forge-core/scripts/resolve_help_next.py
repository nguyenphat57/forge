from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import configure_stdio, load_preferences, resolve_response_style


MARKER_FILES = (
    "README.md",
    "README",
    "package.json",
    "pyproject.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
)

MARKER_DIRS = (
    "docs",
    "src",
    "app",
    "tests",
)


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


def find_latest_markdown(workspace: Path, relative_dir: str) -> Path | None:
    base_dir = workspace / relative_dir
    if not base_dir.exists():
        return None
    candidates = sorted(
        base_dir.rglob("*.md"),
        key=lambda path: (path.stat().st_mtime, str(path).lower()),
        reverse=True,
    )
    return candidates[0] if candidates else None


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
        if not stripped:
            continue
        if stripped.upper() == "HANDOVER":
            continue
        if stripped.startswith("- "):
            return stripped[2:].strip()
        return stripped
    return None


def read_git_status(workspace: Path, warnings: list[str]) -> dict:
    root_check = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if root_check.returncode != 0:
        return {"available": False, "changed_files": [], "untracked_files": []}

    git_root = root_check.stdout.strip()
    if not git_root or Path(git_root).resolve() != workspace.resolve():
        return {"available": False, "changed_files": [], "untracked_files": []}

    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return {"available": False, "changed_files": [], "untracked_files": []}

    changed_files: list[str] = []
    untracked_files: list[str] = []
    for line in completed.stdout.splitlines():
        entry = line.rstrip()
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:].strip()
        if status == "??":
            untracked_files.append(path)
            continue
        changed_files.append(path)
    return {
        "available": True,
        "changed_files": changed_files,
        "untracked_files": untracked_files,
    }


def session_task(session: dict | None) -> str | None:
    if not session:
        return None
    working_on = session.get("working_on")
    if isinstance(working_on, dict):
        task = working_on.get("task")
        if isinstance(task, str) and task.strip():
            return task.strip()
        feature = working_on.get("feature")
        if isinstance(feature, str) and feature.strip():
            return feature.strip()
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


def determine_stage(
    *,
    session: dict | None,
    git_state: dict,
    latest_plan: Path | None,
    latest_spec: Path | None,
) -> str:
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
        if latest_plan is not None:
            return f"Plan: {extract_markdown_title(latest_plan)}"
        return f"Spec: {extract_markdown_title(latest_spec)}"
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
        primary = f"Resolve the blocker first: {blocker}."
        alternatives = []
        if plan_title:
            alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' to confirm the intended recovery path.")
        alternatives.append("If the blocker keeps drifting, capture a fresh handover with the missing evidence.")
        return "debug", primary, alternatives[:2]

    if stage == "session-active":
        primary = (
            f"Resume the highest-signal pending task: {pending[0]}."
            if pending
            else f"Continue the active task: {session_task(session)}."
        )
        alternatives: list[str] = []
        if len(pending) > 1:
            alternatives.append(f"Continue secondary pending task: {pending[1]}.")
        if plan_title:
            alternatives.append(f"Re-open the latest {plan_kind} '{plan_title}' if priorities changed.")
        if mode == "next":
            alternatives = alternatives[:1]
        return "session", primary, alternatives[:2]

    if stage == "active-changes":
        primary = "Review the current changed files and run the nearest verification before adding new edits."
        alternatives = []
        if plan_title:
            alternatives.append(f"Update the latest {plan_kind} '{plan_title}' if the current diff drifted from the intended slice.")
        alternatives.append("If the slice is already complete, run a review pass and decide whether to merge or continue.")
        if mode == "next":
            alternatives = alternatives[:1]
        return "review", primary, alternatives[:2]

    if stage == "planned":
        label = plan_title or "the latest plan"
        primary = f"Start the first concrete slice from {plan_kind} '{label}'."
        alternatives = [
            "If scope is still fuzzy, tighten the plan before writing code.",
            "If repo health is unclear, run a review-style scan before implementation.",
        ]
        if mode == "next":
            alternatives = alternatives[:1]
        return "plan", primary, alternatives[:2]

    primary = "Start from README, package manifests, and docs/plans to identify the active workflow."
    alternatives = [
        "If you already know the task, state it directly and let Forge route the right workflow.",
        "If the repo feels unhealthy, run a review-style scan before new implementation.",
    ]
    if mode == "next":
        alternatives = alternatives[:1]
    return "review", primary, alternatives[:2]


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
        evidence.append(
            "git: {count} working tree item(s)".format(
                count=len(git_state["changed_files"]) + len(git_state["untracked_files"])
            )
        )
    if preferences_source["path"]:
        evidence.append(f"preferences: {preferences_source['path']}")
    return evidence


def build_report(workspace: Path, mode: str) -> dict:
    warnings: list[str] = []
    preferences_report = load_preferences(workspace=workspace)
    response_style = resolve_response_style(preferences_report["preferences"])
    warnings.extend(preferences_report["warnings"])

    readme = first_existing_file(workspace, ("README.md", "README"))
    latest_plan = find_latest_markdown(workspace, "docs/plans")
    latest_spec = find_latest_markdown(workspace, "docs/specs")
    session_path = workspace / ".brain" / "session.json"
    session = read_json_object(session_path, "session context", warnings)
    handover_path = workspace / ".brain" / "handover.md"
    handover_excerpt = read_handover_excerpt(handover_path)
    git_state = read_git_status(workspace, warnings)
    repo_signals = collect_repo_signals(workspace)

    stage = determine_stage(session=session, git_state=git_state, latest_plan=latest_plan, latest_spec=latest_spec)
    if stage == "unscoped":
        warnings.append("No session context found.")
        warnings.append("No active plan or spec found.")

    focus = build_focus(stage, session=session, latest_plan=latest_plan, latest_spec=latest_spec, git_state=git_state)
    suggested_workflow, recommended_action, alternatives = build_recommendations(
        mode=mode,
        stage=stage,
        session=session,
        latest_plan=latest_plan,
        latest_spec=latest_spec,
        handover_excerpt=handover_excerpt,
    )

    status = "WARN" if warnings else "PASS"
    return {
        "status": status,
        "mode": mode,
        "workspace": str(workspace),
        "current_stage": stage,
        "current_focus": focus,
        "suggested_workflow": suggested_workflow,
        "recommended_action": recommended_action,
        "alternatives": alternatives,
        "signals": {
            "repo_signals": repo_signals,
            "changed_files": git_state["changed_files"],
            "untracked_files": git_state["untracked_files"],
            "latest_plan": str(latest_plan) if latest_plan else None,
            "latest_plan_title": extract_markdown_title(latest_plan),
            "latest_spec": str(latest_spec) if latest_spec else None,
            "latest_spec_title": extract_markdown_title(latest_spec),
            "session_file": str(session_path) if session_path.exists() else None,
            "handover_file": str(handover_path) if handover_path.exists() else None,
            "readme": str(readme) if readme else None,
        },
        "evidence": build_evidence(
            readme=readme,
            latest_plan=latest_plan,
            latest_spec=latest_spec,
            session_path=session_path,
            handover_path=handover_path,
            git_state=git_state,
            preferences_source=preferences_report["source"],
        ),
        "response_style": response_style,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Help/Next",
        f"- Status: {report['status']}",
        f"- Mode: {report['mode']}",
        f"- Workspace: {report['workspace']}",
        f"- Stage: {report['current_stage']}",
        f"- Focus: {report['current_focus']}",
        f"- Suggested workflow: {report['suggested_workflow']}",
        f"- Recommended action: {report['recommended_action']}",
    ]
    if report["alternatives"]:
        lines.append("- Alternatives:")
        for item in report["alternatives"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Alternatives: (none)")
    lines.append("- Evidence:")
    for item in report["evidence"]:
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

    parser = argparse.ArgumentParser(description="Resolve a host-neutral help/next recommendation from workspace state.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root to inspect")
    parser.add_argument("--mode", choices=["help", "next"], required=True, help="Navigator mode")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve(), args.mode)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
