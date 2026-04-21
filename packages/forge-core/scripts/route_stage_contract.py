from __future__ import annotations

from common import normalize_text, score_keywords
from route_intent_detection import infer_change_type
from route_risk import should_insert_brainstorm


def _haystacks(prompt_text: str, repo_signals: list[str]) -> tuple[str, str]:
    return normalize_text(prompt_text), normalize_text(" ".join(repo_signals))


def _stage_definition(registry: dict, stage_name: str) -> dict:
    profile_config = registry.get("solo_profiles", {})
    stages = profile_config.get("stages", {})
    return stages.get(stage_name, {"workflow": stage_name})


def _append_stage(
    decisions: list[dict],
    registry: dict,
    stage_name: str,
    *,
    status: str,
    activation_reason: str | None = None,
    skip_reason: str | None = None,
    mode: str | None = None,
) -> None:
    stage = _stage_definition(registry, stage_name)
    entry = {
        "stage": stage_name,
        "workflow": stage.get("workflow", stage_name),
        "status": status,
    }
    if activation_reason:
        entry["activation_reason"] = activation_reason
    if skip_reason:
        entry["skip_reason"] = skip_reason
    if mode:
        entry["mode"] = mode
    decisions.append(entry)


def resolve_profile(prompt_text: str, repo_signals: list[str], registry: dict) -> tuple[str, dict]:
    profile_config = registry.get("solo_profiles", {})
    prompt_haystack, signal_haystack = _haystacks(prompt_text, repo_signals)
    public_prompt = score_keywords(prompt_haystack, profile_config.get("public_markers", [])) > 0
    public_signal = score_keywords(signal_haystack, profile_config.get("public_repo_signals", [])) > 0
    profile = "solo-public" if public_prompt or public_signal else profile_config.get("default_profile", "solo-internal")
    return profile, profile_config.get("profiles", {}).get(profile, {})


def _looks_like_greenfield_feature(prompt_text: str, intent: str) -> bool:
    if intent != "BUILD":
        return False
    normalized = normalize_text(prompt_text)
    if score_keywords(normalized, ["existing clients", "existing client", "backward compatibility", "keep backward", "compatibility"]) > 0:
        return False
    return score_keywords(
        normalized,
        [
            "new feature",
            "new flow",
            "new screen",
            "new module",
            "add a new",
            "create a new",
            "greenfield",
        ],
    ) > 0


def _looks_like_ui_work(prompt_text: str, repo_signals: list[str], registry: dict) -> bool:
    prompt_haystack, signal_haystack = _haystacks(prompt_text, repo_signals)
    ui_detection = registry.get("ui_detection", {})
    prompt_score = score_keywords(prompt_haystack, ui_detection.get("prompt_keywords", []))
    signal_score = score_keywords(signal_haystack, ui_detection.get("repo_signals", []))
    weak_signal_score = score_keywords(signal_haystack, ui_detection.get("weak_repo_signals", []))
    return prompt_score > 0 or max(signal_score - weak_signal_score, 0) > 0


def _interaction_model_change(prompt_text: str) -> bool:
    normalized = normalize_text(prompt_text)
    return score_keywords(
        normalized,
        [
            "interaction",
            "screen",
            "layout",
            "flow",
            "touch",
            "tablet",
            "dashboard",
            "form",
            "responsive",
            "ux",
            "ui",
        ],
    ) > 0


def _system_shape_change(prompt_text: str, complexity: str) -> bool:
    normalized = normalize_text(prompt_text)
    if complexity == "large":
        return True
    return score_keywords(normalized, ["architecture", "state sync", "data flow", "auth model", "system shape"]) > 0


def _packet_unclear(prompt_text: str, registry: dict) -> bool:
    normalized = normalize_text(prompt_text)
    return score_keywords(normalized, registry.get("solo_profiles", {}).get("packet_unclear_markers", [])) > 0


def _requires_brainstorm_design_doc(intent: str, prompt_text: str, registry: dict) -> bool:
    if intent == "VISUALIZE":
        return True
    return intent == "BUILD" and infer_change_type(prompt_text, registry) == "behavioral"


def _release_context(
    prompt_text: str,
    repo_signals: list[str],
    intent: str,
    profile: str,
    quality_profile_key: str,
    registry: dict,
) -> dict:
    profile_config = registry.get("solo_profiles", {})
    prompt_haystack, signal_haystack = _haystacks(prompt_text, repo_signals)
    release_candidate = intent == "DEPLOY" or score_keywords(prompt_haystack, profile_config.get("release_markers", [])) > 0
    shared_env_release = profile == "solo-internal" and release_candidate
    public_release = profile == "solo-public" and release_candidate
    critical_internal_release = shared_env_release and (
        quality_profile_key in {"release-critical", "migration-critical"}
        or score_keywords(prompt_haystack, profile_config.get("critical_internal_markers", [])) > 0
    )
    release_surface_change = release_candidate or (
        score_keywords(prompt_haystack, profile_config.get("release_surface_prompt_keywords", [])) > 0
        or score_keywords(signal_haystack, profile_config.get("release_surface_repo_signals", [])) > 0
    )
    return {
        "release_candidate": release_candidate,
        "shared_env_release": shared_env_release,
        "public_release": public_release,
        "critical_internal_release": critical_internal_release,
        "release_surface_change": release_surface_change,
        "broad_public_release": public_release and (
            score_keywords(prompt_haystack, ["production", "public rollout", "broad rollout", "general availability", "ga", "launch"]) > 0
        ),
    }


def _active_chain(decisions: list[dict], field: str) -> list[str]:
    chain: list[str] = []
    for item in decisions:
        if item["status"] == "skipped":
            continue
        value = str(item[field])
        if chain and chain[-1] == value:
            continue
        chain.append(value)
    return chain


def build_required_stages(
    prompt_text: str,
    repo_signals: list[str],
    intent: str,
    complexity: str,
    quality_profile_key: str,
    registry: dict,
) -> dict:
    profile, profile_definition = resolve_profile(prompt_text, repo_signals, registry)
    order = list(profile_definition.get("intent_orders", {}).get(intent, []))
    ui_work = _looks_like_ui_work(prompt_text, repo_signals, registry)
    interaction_model_change = _interaction_model_change(prompt_text)
    greenfield_feature = _looks_like_greenfield_feature(prompt_text, intent)
    brainstorm_required = _requires_brainstorm_design_doc(intent, prompt_text, registry) or should_insert_brainstorm(
        prompt_text,
        intent,
        complexity,
        registry,
    )
    brainstorm_mode = "discovery-full" if brainstorm_required and (
        complexity == "large"
        or score_keywords(normalize_text(prompt_text), ["workflow", "approval flow", "multiple actors", "journey", "process"]) > 0
    ) else "discovery-lite"
    architect_lens = _system_shape_change(prompt_text, complexity) and intent in {"BUILD", "VISUALIZE", "DEBUG"}
    release_context = _release_context(prompt_text, repo_signals, intent, profile, quality_profile_key, registry)
    secure_required = (
        release_context["public_release"]
        or release_context["critical_internal_release"]
    )
    if intent == "REVIEW":
        secure_required = True
    visualize_lens = intent == "VISUALIZE" or (
        intent == "BUILD" and ui_work and complexity in {"medium", "large"} and interaction_model_change
    )
    optional_design_lenses: list[str] = []
    if visualize_lens:
        optional_design_lenses.append("visualize")
    if architect_lens:
        optional_design_lenses.append("architect")
    self_review_required = intent in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"} and (
        complexity in {"medium", "large"} or release_context["release_candidate"]
    )
    quality_gate_required = intent in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"} and (
        complexity in {"medium", "large"} or release_context["release_candidate"]
    )
    deploy_required = release_context["release_candidate"]

    decisions: list[dict] = []
    for stage_name in order:
        if stage_name == "brainstorm":
            if intent not in {"BUILD", "VISUALIZE"}:
                continue
            if brainstorm_required:
                reason = "greenfield_feature" if greenfield_feature else "default_chain"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason, mode=brainstorm_mode)
            elif complexity in {"medium", "large"} or intent == "VISUALIZE":
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="direction_locked")
            continue

        if stage_name == "plan":
            if intent in {"BUILD", "VISUALIZE"} or (intent == "DEBUG" and complexity == "large"):
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "visualize":
            continue

        if stage_name == "architect":
            continue

        if stage_name in {"build", "test", "debug", "refactor", "review", "session"}:
            _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "self-review":
            if self_review_required:
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "secure":
            if secure_required:
                reason = "public_release" if release_context["public_release"] else "critical_internal_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            continue

        if stage_name == "quality-gate":
            if quality_gate_required:
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "deploy":
            if deploy_required:
                reason = "public_release" if release_context["public_release"] else "shared_env_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            continue

    return {
        "profile": profile,
        "required_stages": decisions,
        "required_stage_chain": _active_chain(decisions, "stage"),
        "workflow_chain": _active_chain(decisions, "workflow"),
        "optional_design_lenses": optional_design_lenses,
        "release_context": release_context,
    }
