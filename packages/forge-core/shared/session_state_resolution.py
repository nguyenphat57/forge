from __future__ import annotations


def git_worktree_clean(git_state: dict) -> bool:
    return bool(git_state.get("available")) and not git_state.get("changed_files") and not git_state.get("untracked_files")


def git_handoff_clean(git_state: dict) -> bool:
    if not git_worktree_clean(git_state):
        return False
    if git_state.get("synced_with_upstream") is True:
        return True
    upstream = git_state.get("branch_upstream")
    return not (isinstance(upstream, str) and upstream.strip())


def _looks_like_diff_follow_up(text: str) -> bool:
    lowered = text.casefold()
    markers = (
        "staged diff",
        "remaining diff",
        "review diff",
        "git diff",
        "working tree",
        "unstaged",
        "staged change",
    )
    return any(marker in lowered for marker in markers)


def _looks_like_commit_push_follow_up(text: str) -> bool:
    lowered = text.casefold()
    markers = (
        "commit and push",
        "commit/push",
        "commit if approved",
        "push if approved",
        "uncommitted",
        "unpushed",
        "approved handoff",
        "ready-for-merge",
    )
    return any(marker in lowered for marker in markers)


def filter_stale_session_items(items: list[str], git_state: dict, *, risk_mode: bool) -> tuple[list[str], int]:
    clean = git_worktree_clean(git_state)
    handoff_clean = git_handoff_clean(git_state)
    kept: list[str] = []
    filtered = 0
    for item in items:
        stale = False
        if clean and _looks_like_diff_follow_up(item):
            stale = True
        if (handoff_clean if risk_mode else clean and handoff_clean) and _looks_like_commit_push_follow_up(item):
            stale = True
        if stale:
            filtered += 1
            continue
        kept.append(item)
    return kept, filtered


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


def session_status_value(session: dict | None) -> str | None:
    if not isinstance(session, dict):
        return None
    working_on = session.get("working_on")
    if not isinstance(working_on, dict):
        return None
    value = working_on.get("status")
    return value.strip().casefold() if isinstance(value, str) and value.strip() else None


def pending_tasks(session: dict | None) -> list[str]:
    if not isinstance(session, dict):
        return []
    values = session.get("pending_tasks")
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


def filtered_pending_tasks(session: dict | None, git_state: dict) -> list[str]:
    pending = pending_tasks(session)
    kept, _ = filter_stale_session_items(pending, git_state, risk_mode=False)
    return kept
