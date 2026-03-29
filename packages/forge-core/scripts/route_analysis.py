from __future__ import annotations

import re

from common import normalize_text, score_keywords


EDITING_INTENTS = {"BUILD", "DEBUG", "OPTIMIZE"}


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


def detect_complexity(prompt_text: str, changed_files: int | None, registry: dict) -> str:
    normalized = normalize_text(prompt_text)
    quick_requested = normalized.startswith("/quick")
    high_risk_keywords: list[str] = []
    high_risk_keywords.extend(registry["complexity"]["prompt_hints"].get("large", []))
    high_risk_keywords.extend(registry.get("spec_review_gate", {}).get("prompt_keywords", []))
    for profile_name in ("release-critical", "migration-critical", "external-interface"):
        high_risk_keywords.extend(
            registry.get("quality_profiles", {}).get(profile_name, {}).get("prompt_keywords", [])
        )
    quick_high_risk = score_keywords(normalized, high_risk_keywords) > 0

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


def detect_domain_skills(
    prompt_text: str,
    repo_signals: list[str],
    intent: str,
    complexity: str,
    registry: dict,
) -> list[str]:
    normalized_prompt = normalize_text(prompt_text)
    normalized_signals = normalize_text(" ".join(repo_signals))
    prompt_only = uses_prompt_only_scope(
        intent,
        complexity,
        registry,
        "prompt_only_domain_intents",
        "domains",
    )
    domains: list[str] = []
    for domain_name, config in registry.get("domains", {}).items():
        prompt_score = score_keywords(normalized_prompt, config.get("prompt_keywords", []))
        signal_score = score_keywords(normalized_signals, config.get("repo_signals", []))
        weak_signal_score = score_keywords(normalized_signals, config.get("weak_repo_signals", []))
        strong_signal_score = max(signal_score - weak_signal_score, 0)
        if prompt_score > 0 or (not prompt_only and strong_signal_score > 0):
            domains.append(domain_name)
    return domains


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


def choose_verification_profile(
    intent: str,
    prompt_text: str,
    repo_signals: list[str],
    registry: dict,
    has_harness: str,
) -> tuple[str | None, dict | None]:
    if intent not in EDITING_INTENTS:
        return None, None

    change_type = infer_change_type(prompt_text, registry)
    if change_type == "non_behavioral":
        key = "non_behavioral"
    elif infer_harness(has_harness, prompt_text, repo_signals):
        key = "behavioral_with_harness"
    else:
        key = "behavioral_reproduction_first"
    return key, registry["verification_profiles"][key]


def choose_execution_mode(prompt_text: str, intent: str, complexity: str, registry: dict) -> str | None:
    if intent not in EDITING_INTENTS:
        return None
    if complexity == "small":
        return "single-track"

    normalized = normalize_text(prompt_text)
    modes = registry.get("execution_modes", {})
    best_mode = "single-track"
    best_score = -1

    for mode_name, config in modes.items():
        if complexity not in config.get("recommended_for", []):
            continue
        score = score_keywords(normalized, config.get("prompt_keywords", []))
        if complexity == "large" and mode_name == "checkpoint-batch":
            score += 1
        if score > best_score:
            best_mode = mode_name
            best_score = score

    return best_mode


def choose_quality_profile(
    prompt_text: str,
    repo_signals: list[str],
    intent: str,
    complexity: str,
    registry: dict,
) -> tuple[str, dict]:
    normalized_prompt = normalize_text(prompt_text)
    normalized_signals = normalize_text(" ".join(repo_signals))
    profiles = registry.get("quality_profiles", {})
    priority = registry.get("quality_profile_priority", list(profiles.keys()))
    intent_preferences = registry.get("quality_profile_intent_preference", {})
    priority_rank = {name: index for index, name in enumerate(priority)}
    prompt_only = uses_prompt_only_scope(
        intent,
        complexity,
        registry,
        "prompt_only_quality_profile_intents",
        "quality_profiles",
    )

    best_name = "standard"
    best_score = 0
    best_rank = priority_rank.get("standard", len(priority_rank))

    for profile_name, config in profiles.items():
        if profile_name == "standard":
            continue

        prompt_score = score_keywords(normalized_prompt, config.get("prompt_keywords", []))
        if prompt_only and prompt_score <= 0:
            continue

        evidence_score = prompt_score
        if not prompt_only or prompt_score > 0:
            evidence_score += score_keywords(normalized_signals, config.get("repo_signals", []))
        if evidence_score <= 0:
            continue

        score = evidence_score * 10
        if intent in config.get("intent_bias", []):
            score += config.get("intent_boost", 1)
        if profile_name in intent_preferences.get(intent, []):
            score += 100

        rank = priority_rank.get(profile_name, len(priority_rank))
        if score > best_score or (score == best_score and rank < best_rank):
            best_name = profile_name
            best_score = score
            best_rank = rank

    return best_name, profiles[best_name]


def requires_change_artifacts(intent: str, complexity: str) -> bool:
    return intent in EDITING_INTENTS and complexity in {"medium", "large"}
