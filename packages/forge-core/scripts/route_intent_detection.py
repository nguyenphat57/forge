from __future__ import annotations

import re

from common import normalize_text, score_keywords


def uses_prompt_only_scope(intent: str, complexity: str, registry: dict, intent_key: str, small_key: str) -> bool:
    policy = registry.get("minimal_routing_policy", {})
    if intent in policy.get(intent_key, []):
        return True
    return complexity == "small" and policy.get("prompt_only_for_small", {}).get(small_key, False)


def keyword_position(keyword: str, text: str) -> int | None:
    if not keyword:
        return None
    if any(char in keyword for char in ("/", ".", "_")):
        position = text.find(keyword)
        return position if position >= 0 else None
    pattern = r"(?<!\w){0}(?!\w)".format(re.escape(keyword))
    match = re.search(pattern, text)
    return match.start() if match else None


def keyword_match_metadata(text: str, keywords: list[str]) -> tuple[int, int | None, int]:
    seen: set[str] = set()
    score = 0
    first_position: int | None = None
    longest_match = 0

    for keyword in keywords:
        normalized = normalize_text(keyword)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        position = keyword_position(normalized, text)
        if position is None:
            continue
        score += 1
        if first_position is None or position < first_position:
            first_position = position
        longest_match = max(longest_match, len(normalized))

    return score, first_position, longest_match


def detect_intent(prompt_text: str, registry: dict) -> tuple[str, dict]:
    normalized = normalize_text(prompt_text)
    best_intent = "BUILD"
    best_score = -1
    best_tiebreak = (-1, -1, -1)

    for intent, config in registry["intents"].items():
        keyword_score, first_position, longest_match = keyword_match_metadata(
            normalized,
            config.get("keywords", []),
        )
        shortcut_match = any(
            normalized.startswith(normalize_text(shortcut))
            for shortcut in config.get("shortcuts", [])
        )
        score = keyword_score + (10 if shortcut_match else 0)
        tiebreak = (
            1 if shortcut_match else 0,
            -(first_position if first_position is not None else len(normalized) + 1),
            longest_match,
        )
        if score > best_score or (score == best_score and score > 0 and tiebreak > best_tiebreak):
            best_intent = intent
            best_score = score
            best_tiebreak = tiebreak

    return best_intent, registry["intents"][best_intent]


def detect_session_mode(prompt_text: str, registry: dict) -> str | None:
    normalized = normalize_text(prompt_text)
    modes = registry.get("session_modes", {})
    best_mode: str | None = None
    best_score = -1
    best_tiebreak = (-1, -1, -1)

    for mode_name, config in modes.items():
        keyword_score, first_position, longest_match = keyword_match_metadata(
            normalized,
            config.get("keywords", []),
        )
        shortcut_match = any(
            normalized.startswith(normalize_text(shortcut))
            for shortcut in config.get("shortcuts", [])
        )
        score = keyword_score + (10 if shortcut_match else 0)
        tiebreak = (
            1 if shortcut_match else 0,
            -(first_position if first_position is not None else len(normalized) + 1),
            longest_match,
        )
        if score > best_score or (score == best_score and score > 0 and tiebreak > best_tiebreak):
            best_mode = mode_name
            best_score = score
            best_tiebreak = tiebreak

    return best_mode or "restore"


def detect_complexity(prompt_text: str, changed_files: int | None, registry: dict) -> str:
    normalized = normalize_text(prompt_text)
    quick_requested = normalized.startswith("/quick")
    quick_blockers = registry["complexity"]["prompt_hints"].get("large", [])
    quick_high_risk = score_keywords(normalized, quick_blockers) > 0

    if quick_requested and not quick_high_risk:
        return "small"

    if changed_files is not None:
        thresholds = registry["complexity"]["thresholds"]
        if changed_files <= thresholds["small_max_changed_files"]:
            return "small"
        if changed_files <= thresholds["medium_max_changed_files"]:
            return "medium"
        return "large"

    hints = registry["complexity"]["prompt_hints"]
    scores = {
        "small": score_keywords(normalized, hints.get("small", [])),
        "medium": score_keywords(normalized, hints.get("medium", [])),
        "large": score_keywords(normalized, hints.get("large", [])),
    }

    if quick_requested and quick_high_risk and scores["large"] == 0:
        return "medium"
    if scores["large"] > 0:
        return "large"
    if scores["small"] > 0 and scores["medium"] == 0:
        return "small"
    if scores["medium"] > 0:
        return "medium"
    return registry["complexity"]["default"]


def infer_change_type(prompt_text: str, registry: dict) -> str:
    normalized = normalize_text(prompt_text)
    non_behavioral = score_keywords(normalized, registry["change_type_hints"]["non_behavioral_keywords"])
    behavioral = score_keywords(normalized, registry["change_type_hints"]["behavioral_keywords"])
    if non_behavioral > behavioral:
        return "non_behavioral"
    return "behavioral"


def infer_harness(has_harness: str, prompt_text: str, repo_signals: list[str]) -> bool:
    if has_harness == "yes":
        return True
    if has_harness == "no":
        return False

    haystack = normalize_text(" ".join([prompt_text, *repo_signals]))
    harness_markers = [
        "test",
        "spec",
        "vitest",
        "jest",
        "playwright",
        "cypress",
        "pytest",
        "junit",
        "__tests__",
        "tests/",
        ".test.",
        ".spec.",
    ]
    return any(marker in haystack for marker in harness_markers)
