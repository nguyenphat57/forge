from __future__ import annotations

from common import normalize_text, score_keywords
from route_intent_detection import infer_change_type, infer_harness, uses_prompt_only_scope


EDITING_INTENTS = {"BUILD", "DEBUG", "OPTIMIZE"}


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


def process_precheck_required(intent: str, prompt_text: str, registry: dict) -> bool:
    if intent == "VISUALIZE":
        return True
    if intent not in EDITING_INTENTS:
        return False
    return infer_change_type(prompt_text, registry) == "behavioral"


def baseline_required(intent: str, complexity: str) -> bool:
    return intent in EDITING_INTENTS and complexity in {"medium", "large"}


def review_artifact_required(intent: str, complexity: str, execution_pipeline_key: str | None) -> bool:
    return intent in EDITING_INTENTS and (
        complexity in {"medium", "large"} or execution_pipeline_key in {"implementer-quality", "implementer-spec-quality"}
    )


def recommended_isolation_stance(
    intent: str,
    complexity: str,
    execution_mode: str | None,
    host_supports_subagents: bool,
) -> str | None:
    if intent not in EDITING_INTENTS:
        return None
    if complexity == "small":
        return "same-tree"
    if execution_mode == "parallel-safe" and host_supports_subagents:
        return "subagent-split"
    return "worktree"
