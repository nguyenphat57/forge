from __future__ import annotations

from common import normalize_text, score_keywords
from route_risk import matched_high_risk_categories, should_insert_brainstorm, should_insert_spec_review


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


def _looks_like_ui_work(prompt_text: str, domain_skills: list[str], registry: dict) -> bool:
    if "frontend" in domain_skills:
        return True
    normalized = normalize_text(prompt_text)
    frontend_keywords = registry.get("domains", {}).get("frontend", {}).get("prompt_keywords", [])
    return score_keywords(normalized, frontend_keywords) > 0


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


def _system_shape_change(prompt_text: str, quality_profile_key: str, risk_categories: list[str], complexity: str) -> bool:
    normalized = normalize_text(prompt_text)
    if complexity == "large":
        return True
    if quality_profile_key == "migration-critical":
        return True
    if any(category in risk_categories for category in ("data_schema", "integration")):
        return True
    return score_keywords(normalized, ["architecture", "state sync", "data flow", "auth model", "system shape"]) > 0


def _change_artifact_present(prompt_text: str, complexity: str, registry: dict) -> bool:
    if complexity == "small":
        return False
    normalized = normalize_text(prompt_text)
    return score_keywords(normalized, registry.get("solo_profiles", {}).get("change_artifact_markers", [])) > 0


def _packet_unclear(prompt_text: str, registry: dict) -> bool:
    normalized = normalize_text(prompt_text)
    return score_keywords(normalized, registry.get("solo_profiles", {}).get("packet_unclear_markers", [])) > 0


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
    domain_skills: list[str],
    quality_profile_key: str,
    registry: dict,
) -> dict:
    profile, profile_definition = resolve_profile(prompt_text, repo_signals, registry)
    order = list(profile_definition.get("intent_orders", {}).get(intent, []))
    risk_categories = matched_high_risk_categories(prompt_text, repo_signals)
    non_behavioral = score_keywords(
        normalize_text(prompt_text),
        registry.get("change_type_hints", {}).get("non_behavioral_keywords", []),
    ) > 0
    effective_risk_categories = [] if non_behavioral else risk_categories
    ui_work = _looks_like_ui_work(prompt_text, domain_skills, registry)
    interaction_model_change = _interaction_model_change(prompt_text)
    greenfield_feature = _looks_like_greenfield_feature(prompt_text, intent)
    brainstorm_required = should_insert_brainstorm(prompt_text, intent, complexity, registry) or (
        greenfield_feature and complexity in {"medium", "large"}
    )
    brainstorm_mode = "discovery-full" if brainstorm_required and (
        complexity == "large"
        or score_keywords(normalize_text(prompt_text), ["workflow", "approval flow", "multiple actors", "journey", "process"]) > 0
    ) else "discovery-lite"
    packet_unclear = _packet_unclear(prompt_text, registry)
    spec_review_required = should_insert_spec_review(prompt_text, repo_signals, intent, complexity, registry)
    if intent == "BUILD" and complexity == "small":
        spec_review_required = spec_review_required and packet_unclear
    architect_required = _system_shape_change(prompt_text, quality_profile_key, effective_risk_categories, complexity)
    change_artifact_present = _change_artifact_present(prompt_text, complexity, registry)
    release_context = _release_context(prompt_text, repo_signals, intent, profile, quality_profile_key, registry)
    secure_required = (
        release_context["public_release"]
        or release_context["critical_internal_release"]
        or any(category in effective_risk_categories for category in ("auth_payment", "data_schema", "integration"))
        or (quality_profile_key == "migration-critical" and complexity in {"medium", "large"})
        or (quality_profile_key == "release-critical" and release_context["release_candidate"])
    )
    if intent == "REVIEW":
        secure_required = True
    visualize_required = intent == "VISUALIZE" or (
        intent == "BUILD" and ui_work and complexity in {"medium", "large"} and interaction_model_change
    )
    self_review_required = intent in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"} and (
        complexity in {"medium", "large"} or release_context["release_candidate"]
    )
    review_pack_required = release_context["public_release"] or release_context["shared_env_release"]
    verify_change_required = change_artifact_present
    quality_gate_required = intent in {"BUILD", "DEBUG", "OPTIMIZE", "DEPLOY"} and (
        complexity in {"medium", "large"} or release_context["release_candidate"]
    )
    release_doc_sync_required = release_context["release_surface_change"] and (
        release_context["public_release"] or release_context["shared_env_release"] or release_context["critical_internal_release"]
    )
    release_readiness_required = release_context["public_release"] or release_context["critical_internal_release"]
    deploy_required = release_context["release_candidate"]
    adoption_check_required = release_context["public_release"] or release_context["shared_env_release"]

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
            if visualize_required:
                reason = "interaction_model_change" if interaction_model_change else "ui_medium_plus"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif intent in {"BUILD", "VISUALIZE"}:
                _append_stage(
                    decisions,
                    registry,
                    stage_name,
                    status="skipped",
                    skip_reason="direction_locked" if ui_work else "non_ui",
                )
            continue

        if stage_name == "architect":
            if architect_required and intent in {"BUILD", "VISUALIZE", "DEBUG"}:
                reason = "boundary_risk" if risk_categories else "default_chain"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif intent in {"BUILD", "VISUALIZE", "DEBUG"} and complexity in {"medium", "large"}:
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="packet_clear")
            continue

        if stage_name == "spec-review":
            if spec_review_required:
                reason = "packet_unclear" if packet_unclear and not risk_categories else "boundary_risk" if risk_categories else "default_chain"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif intent in {"BUILD", "DEBUG"} and (complexity in {"medium", "large"} or risk_categories or packet_unclear):
                _append_stage(
                    decisions,
                    registry,
                    stage_name,
                    status="skipped",
                    skip_reason="packet_clear" if packet_unclear else "low_risk_boundary",
                )
            continue

        if stage_name == "change":
            if intent != "BUILD":
                continue
            if change_artifact_present:
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="change_artifact_present")
            elif complexity in {"medium", "large"}:
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="no_change_artifact")
            continue

        if stage_name in {"build", "test", "debug", "refactor", "review", "session"}:
            _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "review-pack":
            if review_pack_required:
                reason = "public_release" if release_context["public_release"] else "shared_env_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif release_context["release_candidate"] or intent in {"BUILD", "DEBUG", "DEPLOY"}:
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="no_shared_env")
            continue

        if stage_name == "self-review":
            if self_review_required:
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "secure":
            if secure_required:
                reason = "public_release" if release_context["public_release"] else "boundary_risk"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif intent in {"BUILD", "DEBUG", "DEPLOY"} and (complexity in {"medium", "large"} or release_context["release_candidate"]):
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="low_risk_boundary")
            continue

        if stage_name == "verify-change":
            if verify_change_required:
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="change_artifact_present")
            elif intent == "BUILD" and complexity in {"medium", "large"}:
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="no_change_artifact")
            continue

        if stage_name == "quality-gate":
            if quality_gate_required:
                _append_stage(decisions, registry, stage_name, status="required", activation_reason="default_chain")
            continue

        if stage_name == "release-doc-sync":
            if release_doc_sync_required:
                if release_context["public_release"]:
                    reason = "public_release"
                elif release_context["critical_internal_release"]:
                    reason = "critical_internal_release"
                else:
                    reason = "shared_env_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif intent in {"BUILD", "DEBUG", "DEPLOY"} and (release_context["release_candidate"] or complexity in {"medium", "large"}):
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="no_release_surface")
            continue

        if stage_name == "release-readiness":
            if release_readiness_required:
                reason = "public_release" if release_context["public_release"] else "critical_internal_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            elif release_context["shared_env_release"] or intent == "DEPLOY":
                _append_stage(decisions, registry, stage_name, status="skipped", skip_reason="not_public_release")
            continue

        if stage_name == "deploy":
            if deploy_required:
                reason = "public_release" if release_context["public_release"] else "shared_env_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)
            continue

        if stage_name == "adoption-check":
            if adoption_check_required:
                reason = "public_release" if release_context["public_release"] else "shared_env_release"
                _append_stage(decisions, registry, stage_name, status="required", activation_reason=reason)

    return {
        "profile": profile,
        "required_stages": decisions,
        "required_stage_chain": _active_chain(decisions, "stage"),
        "workflow_chain": _active_chain(decisions, "workflow"),
        "change_artifact_present": change_artifact_present,
        "release_context": release_context,
    }
