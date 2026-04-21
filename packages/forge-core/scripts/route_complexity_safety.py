from __future__ import annotations

from common import normalize_text, score_keywords


COMPLEXITY_RANK = {"small": 0, "medium": 1, "large": 2}


def _at_least(current: str, minimum: str) -> str:
    if COMPLEXITY_RANK.get(current, 0) >= COMPLEXITY_RANK.get(minimum, 0):
        return current
    return minimum


def _threshold_reached(value: int | None, threshold: int | None) -> bool:
    return isinstance(value, int) and isinstance(threshold, int) and value >= threshold


def _gate_matches(prompt_text: str, repo_signals: list[str], config: dict) -> bool:
    prompt_haystack = normalize_text(prompt_text)
    signal_haystack = normalize_text(" ".join(repo_signals))
    return (
        score_keywords(prompt_haystack, config.get("prompt_markers", [])) > 0
        or score_keywords(signal_haystack, config.get("repo_signal_markers", [])) > 0
    )


def audit_complexity(
    *,
    initial_complexity: str,
    prompt_text: str,
    repo_signals: list[str],
    changed_files: int | None,
    recent_small_tasks: int | None,
    changed_files_since_review: int | None,
    registry: dict,
) -> dict:
    safety = registry.get("complexity", {}).get("safety_gates", {})
    blast_radius = safety.get("blast_radius", {})
    accumulation = safety.get("accumulation", {})
    final_complexity = initial_complexity
    reasons: list[str] = []

    for minimum in ("large", "medium"):
        config = blast_radius.get(minimum, {})
        if isinstance(config, dict) and _gate_matches(prompt_text, repo_signals, config):
            final_complexity = _at_least(final_complexity, minimum)
            reason = config.get("reason")
            if isinstance(reason, str) and reason:
                reasons.append(reason)

    if _threshold_reached(recent_small_tasks, accumulation.get("recent_small_task_threshold")):
        final_complexity = _at_least(final_complexity, accumulation.get("minimum_complexity", "medium"))
        reasons.append("accumulation: recent small-task threshold reached")

    if _threshold_reached(changed_files_since_review, accumulation.get("changed_files_since_review_threshold")):
        final_complexity = _at_least(final_complexity, accumulation.get("minimum_complexity", "medium"))
        reasons.append("accumulation: changed-files-since-review threshold reached")

    return {
        "initial_complexity": initial_complexity,
        "final_complexity": final_complexity,
        "escalated": final_complexity != initial_complexity,
        "authority": "diff-and-risk-evidence",
        "changed_files": changed_files,
        "recent_small_tasks": recent_small_tasks,
        "changed_files_since_review": changed_files_since_review,
        "reasons": list(dict.fromkeys(reasons)),
    }
