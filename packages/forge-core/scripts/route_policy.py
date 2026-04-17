from __future__ import annotations

from route_analysis import (
    baseline_required,
    choose_execution_mode,
    choose_quality_profile,
    choose_verification_profile,
    detect_complexity,
    detect_intent,
    detect_session_mode,
    process_precheck_required,
)
from route_execution_advice import (
    build_baseline_verification,
    build_review_sequence,
    build_worktree_bootstrap,
    classify_browser_qa,
    classify_packet_mode,
)
from route_process_requirements import recommended_isolation_stance, review_artifact_required
from route_stage_contract import build_required_stages
from workflow_aliases import resolve_explicit_workflow_alias, strip_explicit_workflow_alias


def _explicit_workflow_contract(workflow_name: str, profile: str) -> dict:
    return {
        "profile": profile,
        "required_stages": [
            {
                "stage": workflow_name,
                "workflow": workflow_name,
                "status": "required",
                "activation_reason": "explicit_alias",
            }
        ],
        "required_stage_chain": [workflow_name],
        "workflow_chain": [workflow_name],
        "release_context": {
            "release_candidate": workflow_name == "deploy",
            "shared_env_release": workflow_name == "deploy",
            "public_release": False,
            "critical_internal_release": False,
            "release_surface_change": workflow_name in {"secure", "quality-gate", "deploy"},
            "broad_public_release": False,
        },
    }


def resolve_route_policy(
    *,
    prompt: str,
    repo_signals: list[str],
    changed_files: int | None,
    has_harness: str,
    registry: dict,
) -> dict:
    explicit_workflow = resolve_explicit_workflow_alias(prompt)
    prompt_for_analysis = strip_explicit_workflow_alias(prompt) if explicit_workflow else prompt
    intent, intent_config = detect_intent(prompt_for_analysis, registry)
    complexity = detect_complexity(prompt_for_analysis, changed_files, registry)
    session_mode = detect_session_mode(prompt_for_analysis, registry) if intent == "SESSION" or explicit_workflow == "session" else None
    verification_key, verification = choose_verification_profile(
        intent,
        prompt_for_analysis,
        repo_signals,
        registry,
        has_harness,
    )
    quality_profile_key, quality_profile = choose_quality_profile(
        prompt_for_analysis,
        repo_signals,
        intent,
        complexity,
        registry,
    )
    stage_contract = build_required_stages(
        prompt_for_analysis,
        repo_signals,
        intent,
        complexity,
        quality_profile_key,
        registry,
    )
    required_stage_contract = (
        _explicit_workflow_contract(explicit_workflow, stage_contract["profile"]) if explicit_workflow else stage_contract
    )
    required_stages = required_stage_contract["required_stages"]
    execution_mode = choose_execution_mode(prompt_for_analysis, intent, complexity, registry)
    precheck_required = process_precheck_required(intent, prompt_for_analysis, registry)
    baseline_proof_required = baseline_required(intent, complexity)
    review_state_required = review_artifact_required(intent, complexity, None, required_stages)
    durable_process_artifacts_required = any(
        isinstance(item, dict)
        and item.get("status") != "skipped"
        and item.get("stage") in {"brainstorm", "spec-review", "self-review", "quality-gate"}
        for item in required_stages
    )
    isolation_recommendation = None
    baseline_verification = None
    worktree_bootstrap = None
    review_sequence: list[dict] = []
    browser_qa = {"classification": "not-needed", "scope": []}
    packet_mode = {"packet_mode": "standard", "eligible": False, "assumptions_first_mode": False, "reasons": []}

    return {
        "intent": intent,
        "intent_config": intent_config,
        "explicit_workflow": explicit_workflow,
        "session_mode": session_mode,
        "complexity": complexity,
        "verification_key": verification_key,
        "verification": verification,
        "quality_profile_key": quality_profile_key,
        "quality_profile": quality_profile,
        "required_stage_contract": required_stage_contract,
        "execution_mode": execution_mode,
        "precheck_required": precheck_required,
        "baseline_proof_required": baseline_proof_required,
        "review_state_required": review_state_required,
        "durable_process_artifacts_required": durable_process_artifacts_required,
        "isolation_recommendation": isolation_recommendation,
        "baseline_verification": baseline_verification,
        "worktree_bootstrap": worktree_bootstrap,
        "review_sequence": review_sequence,
        "browser_qa": browser_qa,
        "packet_mode": packet_mode,
    }


def complete_route_policy(
    *,
    policy: dict,
    execution_pipeline_key: str,
    effective_delegation_mode: str,
    registry: dict,
    prompt: str,
    repo_signals: list[str],
) -> dict:
    required_stages = policy["required_stage_contract"]["required_stages"]
    prompt_for_analysis = strip_explicit_workflow_alias(prompt) if policy.get("explicit_workflow") else prompt
    isolation_recommendation = recommended_isolation_stance(
        policy["intent"],
        policy["complexity"],
        policy["execution_mode"],
        effective_delegation_mode != "controller-baseline",
    )
    baseline_verification = build_baseline_verification(policy["baseline_proof_required"], policy["verification"])
    worktree_bootstrap = build_worktree_bootstrap(isolation_recommendation)
    review_sequence = build_review_sequence(execution_pipeline_key)
    browser_qa = classify_browser_qa(
        prompt_for_analysis,
        intent=policy["intent"],
        complexity=policy["complexity"],
        repo_signals=repo_signals,
        registry=registry,
    )
    packet_mode = classify_packet_mode(
        prompt_for_analysis,
        intent=policy["intent"],
        complexity=policy["complexity"],
        execution_mode=policy["execution_mode"],
        execution_pipeline_key=execution_pipeline_key,
        required_stages=required_stages,
        quality_profile_key=policy["quality_profile_key"],
    )
    return {
        **policy,
        "isolation_recommendation": isolation_recommendation,
        "baseline_verification": baseline_verification,
        "worktree_bootstrap": worktree_bootstrap,
        "review_sequence": review_sequence,
        "browser_qa": browser_qa,
        "packet_mode": packet_mode,
    }
