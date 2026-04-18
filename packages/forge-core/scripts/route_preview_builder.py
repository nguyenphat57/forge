from __future__ import annotations

import argparse

from common import current_bundle_skill_name, detect_runtimes, load_registry, registry_sources, routing_locale_names
from resolve_preferences import build_payload as build_preferences_payload
from route_delegation import (
    choose_delegation_plan,
    choose_execution_pipeline,
    choose_lane_model_assignments,
    resolve_host_capability_tier,
)
from route_local_companions import infer_local_companions, resolve_workspace_router
from route_policy import complete_route_policy, resolve_route_policy


def build_skill_selection_rationale(
    required_stages: list[dict[str, object]],
    registry: dict[str, object],
) -> list[dict[str, str]]:
    reason_labels = registry.get("skill_selection_reason_labels", {})
    rationale: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in required_stages:
        if item.get("status") == "skipped":
            continue
        skill = str(item.get("workflow") or item.get("stage") or "").strip()
        if not skill or skill in seen:
            continue
        seen.add(skill)
        reason_code = str(item.get("activation_reason") or "default_chain")
        reason_text = str(
            reason_labels.get(
                reason_code,
                "selected because the active route requires this stage before completion.",
            )
        )
        rationale.append(
            {
                "skill": skill,
                "reason_code": reason_code,
                "reason": reason_text,
            }
        )
    return rationale


def build_report(args: argparse.Namespace, *, load_registry_fn=load_registry) -> dict:
    registry = load_registry_fn()
    host_capabilities = registry.get("host_capabilities", {})
    host_tier_key, host_tier = resolve_host_capability_tier(host_capabilities if isinstance(host_capabilities, dict) else {})
    host_supports_subagents = bool(host_tier.get("supports_subagents", host_capabilities.get("supports_subagents", False)))
    host_supports_parallel_subagents = bool(
        host_tier.get("supports_parallel_subagents", host_capabilities.get("supports_parallel_subagents", host_supports_subagents))
    )
    workspace_root = getattr(args, "workspace", None)
    if workspace_root is None and args.workspace_router is not None:
        workspace_root = args.workspace_router.parent
    forge_home = getattr(args, "forge_home", None)
    preferences_payload = build_preferences_payload(
        argparse.Namespace(
            workspace=workspace_root,
            forge_home=forge_home,
            preferences_file=None,
            strict=False,
            format="json",
        )
    )
    resolved_delegation_preference = preferences_payload.get("preferences", {}).get("delegation_preference")
    explicit_delegation_preference = getattr(args, "delegation_preference", None)
    if explicit_delegation_preference is not None:
        resolved_delegation_preference = explicit_delegation_preference

    policy = resolve_route_policy(
        prompt=args.prompt,
        repo_signals=args.repo_signal,
        changed_files=args.changed_files,
        has_harness=args.has_harness,
        registry=registry,
    )
    intent = policy["intent"]
    intent_config = policy["intent_config"]
    session_mode = policy["session_mode"]
    complexity = policy["complexity"]
    workspace_router = resolve_workspace_router(args.workspace_router)
    verification_key = policy["verification_key"]
    verification = policy["verification"]
    quality_profile_key = policy["quality_profile_key"]
    quality_profile = policy["quality_profile"]
    required_stage_contract = policy["required_stage_contract"]
    forge_skills = list(required_stage_contract["workflow_chain"]) or list(intent_config["chains"][complexity])
    if intent in {"REVIEW", "SESSION"}:
        forge_skills = list(intent_config["chains"][complexity])
    execution_mode = policy["execution_mode"]
    execution_pipeline_key, execution_pipeline = choose_execution_pipeline(
        intent,
        complexity,
        quality_profile_key,
        forge_skills,
        registry,
    )
    lane_model_assignments = choose_lane_model_assignments(
        forge_skills,
        execution_pipeline_key,
        complexity,
        quality_profile_key,
        registry,
    )
    delegation_strategy, delegation_plan, host_skills = choose_delegation_plan(
        intent,
        execution_mode,
        execution_pipeline_key,
        registry,
        resolved_delegation_preference,
    )
    if isinstance(delegation_plan, dict) and delegation_plan.get("resolved_delegation_preference"):
        resolved_delegation_preference = delegation_plan["resolved_delegation_preference"]
    effective_delegation_mode = (
        delegation_plan.get("effective_delegation_mode")
        if isinstance(delegation_plan, dict)
        else "controller-baseline"
    )
    policy = complete_route_policy(
        policy=policy,
        execution_pipeline_key=execution_pipeline_key,
        effective_delegation_mode=effective_delegation_mode,
        registry=registry,
        prompt=args.prompt,
        repo_signals=args.repo_signal,
    )
    local_companions = infer_local_companions(
        args.prompt,
        args.repo_signal,
        workspace_router,
        intent,
        complexity,
        registry,
    )
    runtimes = detect_runtimes(args.repo_signal, registry)
    active_routing_locales = routing_locale_names()
    required_stages = required_stage_contract["required_stages"]
    skill_selection_rationale = build_skill_selection_rationale(required_stages, registry)
    precheck_required = policy["precheck_required"]
    baseline_proof_required = policy["baseline_proof_required"]
    review_state_required = policy["review_state_required"]
    durable_process_artifacts_required = policy["durable_process_artifacts_required"]
    isolation_recommendation = policy["isolation_recommendation"]
    baseline_verification = policy["baseline_verification"]
    worktree_bootstrap = policy["worktree_bootstrap"]
    review_sequence = policy["review_sequence"]
    browser_qa = policy["browser_qa"]
    packet_mode = policy["packet_mode"]

    return {
        "prompt": args.prompt,
        "repo_signals": args.repo_signal,
        "workspace_router": str(workspace_router) if workspace_router else None,
        "detected": {
            "intent": intent,
            "session_mode": session_mode,
            "complexity": complexity,
            "profile": required_stage_contract["profile"],
            "forge_skills": forge_skills,
            "required_stage_chain": required_stage_contract["required_stage_chain"],
            "required_stages": required_stages,
            "skill_selection_rationale": skill_selection_rationale,
            "host_skills": host_skills,
            "host_supports_subagents": host_supports_subagents,
            "host_supports_parallel_subagents": host_supports_parallel_subagents,
            "host_capability_tier": host_tier_key,
            "host_dispatch_mode": host_tier.get("dispatch_mode"),
            "resolved_delegation_preference": resolved_delegation_preference,
            "effective_delegation_mode": effective_delegation_mode,
            "first_party_companions": [],
            "local_companions": local_companions,
            "runtimes": runtimes,
            "routing_locales": active_routing_locales,
            "verification_profile": verification_key,
            "execution_mode": execution_mode,
            "execution_pipeline": execution_pipeline_key,
            "lane_model_assignments": lane_model_assignments,
            "quality_profile": quality_profile_key,
            "delegation_strategy": delegation_strategy,
            "process_precheck_required": precheck_required,
            "baseline_proof_required": baseline_proof_required,
            "review_artifact_required": review_state_required,
            "durable_process_artifacts_required": durable_process_artifacts_required,
            "isolation_recommendation": isolation_recommendation,
            "baseline_verification": baseline_verification,
            "worktree_bootstrap": worktree_bootstrap,
            "review_sequence": review_sequence,
            "browser_qa_classification": browser_qa["classification"],
            "browser_qa_scope": browser_qa["scope"],
            "packet_mode": packet_mode["packet_mode"],
            "fast_lane_eligible": packet_mode["eligible"],
            "assumptions_first_mode": packet_mode["assumptions_first_mode"],
            "packet_mode_reasons": packet_mode["reasons"],
        },
        "verification": verification,
        "execution_pipeline": execution_pipeline,
        "delegation_plan": delegation_plan,
        "quality_profile": quality_profile,
        "activation_line": "Forge: {intent} | {complexity} | Profile: {profile} | Skills: {skills}".format(
            intent=intent,
            complexity=complexity,
            profile=required_stage_contract["profile"],
            skills=" + ".join([*forge_skills, *host_skills, *local_companions]) or current_bundle_skill_name(),
        ),
        "registry_source": " + ".join(registry_sources()),
    }
