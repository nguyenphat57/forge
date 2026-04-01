from __future__ import annotations


RELEASE_TIER_RULES = {
    "internal-shared": {
        "require_docs_sync": False,
        "require_workspace_canary": False,
        "require_rollout_readiness": False,
        "require_review_pack": False,
        "canary_profile": "controlled-rollout",
        "strict_deploy_gate": False,
    },
    "internal-critical": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": True,
        "require_review_pack": False,
        "canary_profile": "broad",
        "strict_deploy_gate": True,
    },
    "public-controlled": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": False,
        "require_review_pack": True,
        "canary_profile": "controlled-rollout",
        "strict_deploy_gate": True,
    },
    "public-broad": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": True,
        "require_review_pack": True,
        "canary_profile": "broad",
        "strict_deploy_gate": True,
    },
}

BASE_PROFILE_RULES = {
    "solo-internal": dict(RELEASE_TIER_RULES["internal-shared"]),
    "solo-public": dict(RELEASE_TIER_RULES["public-broad"]),
}

LEGACY_PROFILE_HINTS = {
    "standard": {},
    "production": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": True,
        "canary_profile": "broad",
        "strict_deploy_gate": True,
    },
    "auth": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_review_pack": True,
    },
    "billing": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": True,
        "require_review_pack": True,
        "canary_profile": "broad",
    },
}

PROFILE_RULES = {
    **LEGACY_PROFILE_HINTS,
    **BASE_PROFILE_RULES,
}

CANONICAL_SOLO_PROFILES = {"solo-internal", "solo-public"}
COMPATIBILITY_TIER_HINTS = {
    "standard": {
        "solo-internal": "internal-shared",
        "solo-public": "public-controlled",
    },
    "production": {
        "solo-internal": "internal-critical",
        "solo-public": "public-broad",
    },
    "auth": {
        "solo-internal": "internal-critical",
        "solo-public": "public-controlled",
    },
    "billing": {
        "solo-internal": "internal-critical",
        "solo-public": "public-broad",
    },
}


def stage_required(workflow_state: dict | None, stage_name: str) -> bool:
    if not isinstance(workflow_state, dict):
        return False
    stages = workflow_state.get("stages")
    if isinstance(stages, dict):
        payload = stages.get(stage_name)
        if isinstance(payload, dict):
            return payload.get("status") != "skipped"
    required_stage_chain = workflow_state.get("required_stage_chain")
    return isinstance(required_stage_chain, list) and stage_name in required_stage_chain


def workflow_profile(workflow_state: dict | None) -> str | None:
    if not isinstance(workflow_state, dict):
        return None
    resolved = workflow_state.get("profile")
    if isinstance(resolved, str) and resolved in CANONICAL_SOLO_PROFILES:
        return resolved
    return None


def infer_public_surface(public_surface: bool | None, detected_public_surface: bool, workflow_state: dict | None) -> bool:
    if public_surface is not None:
        return bool(public_surface)
    return detected_public_surface or workflow_profile(workflow_state) == "solo-public"


def resolve_compatibility_profile(profile: str, features: set[str], workflow_state: dict | None) -> str | None:
    if profile in LEGACY_PROFILE_HINTS:
        return profile
    if "billing" in features:
        return "billing"
    if "auth" in features:
        return "auth"
    return "standard"


def resolve_effective_profile(
    profile: str,
    features: set[str],
    workflow_state: dict | None,
    *,
    detected_public_surface: bool,
) -> str:
    state_profile = workflow_profile(workflow_state)
    if state_profile:
        return state_profile
    if profile in CANONICAL_SOLO_PROFILES:
        return profile
    if profile == "auto":
        return "solo-public" if detected_public_surface else "solo-internal"
    return "solo-public" if detected_public_surface else "solo-internal"


def resolve_release_tier(
    effective_profile: str,
    compatibility_profile: str | None,
    workflow_state: dict | None,
) -> str:
    state_profile = workflow_profile(workflow_state)
    if state_profile is not None:
        if effective_profile == "solo-public":
            return "public-broad" if stage_required(workflow_state, "release-readiness") else "public-controlled"
        return "internal-critical" if stage_required(workflow_state, "release-readiness") else "internal-shared"

    compatibility_key = compatibility_profile or "standard"
    hints = COMPATIBILITY_TIER_HINTS.get(compatibility_key, COMPATIBILITY_TIER_HINTS["standard"])
    fallback = "public-controlled" if effective_profile == "solo-public" else "internal-shared"
    return hints.get(effective_profile, fallback)


def resolve_profile_rules(
    effective_profile: str,
    workflow_state: dict | None,
    *,
    compatibility_profile: str | None = None,
) -> dict:
    rules = dict(RELEASE_TIER_RULES[resolve_release_tier(effective_profile, compatibility_profile, workflow_state)])
    state_profile = workflow_profile(workflow_state)
    if state_profile is None:
        return rules

    rules["require_docs_sync"] = stage_required(workflow_state, "release-doc-sync")
    rules["require_review_pack"] = stage_required(workflow_state, "review-pack")
    rules["require_rollout_readiness"] = stage_required(workflow_state, "release-readiness")
    rules["require_workspace_canary"] = any(
        stage_required(workflow_state, stage_name)
        for stage_name in ("review-pack", "release-readiness", "deploy", "adoption-check")
    )
    rules["canary_profile"] = "broad" if stage_required(workflow_state, "release-readiness") else "controlled-rollout"
    rules["strict_deploy_gate"] = state_profile == "solo-public"
    return rules
