from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    configure_stdio,
    current_bundle_skill_name,
    default_artifact_dir,
    detect_runtimes,
    load_registry,
    registry_sources,
    routing_locale_names,
    slugify,
    timestamp_slug,
)
from resolve_preferences import build_payload as build_preferences_payload
from route_analysis import (
    baseline_required,
    choose_execution_mode,
    choose_quality_profile,
    choose_verification_profile,
    detect_complexity,
    detect_domain_skills,
    detect_intent,
    process_precheck_required,
)
from route_delegation import (
    choose_delegation_plan,
    choose_execution_pipeline,
    choose_lane_model_assignments,
    resolve_host_capability_tier,
)
from route_execution_advice import (
    build_baseline_verification,
    classify_browser_qa,
    classify_packet_mode,
    build_review_sequence,
    build_worktree_bootstrap,
)
from route_process_requirements import (
    recommended_isolation_stance,
    review_artifact_required,
    requires_change_artifacts,
    verify_change_required,
)
from route_stage_contract import build_required_stages
from companion_matching import match_companions
from route_local_companions import infer_local_companions, resolve_workspace_router
from workflow_state_support import record_workflow_event


def build_report(args: argparse.Namespace) -> dict:
    registry = load_registry()
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
    resolved_delegation_preference = preferences_payload.get("extra", {}).get("delegation_preference")
    explicit_delegation_preference = getattr(args, "delegation_preference", None)
    if explicit_delegation_preference is not None:
        resolved_delegation_preference = explicit_delegation_preference

    intent, intent_config = detect_intent(args.prompt, registry)
    complexity = detect_complexity(args.prompt, args.changed_files, registry)
    workspace_router = resolve_workspace_router(args.workspace_router)
    domain_skills = detect_domain_skills(args.prompt, args.repo_signal, intent, complexity, registry)
    verification_key, verification = choose_verification_profile(
        intent,
        args.prompt,
        args.repo_signal,
        registry,
        args.has_harness,
    )
    quality_profile_key, quality_profile = choose_quality_profile(
        args.prompt,
        args.repo_signal,
        intent,
        complexity,
        registry,
    )
    required_stage_contract = build_required_stages(
        args.prompt,
        args.repo_signal,
        intent,
        complexity,
        domain_skills,
        quality_profile_key,
        registry,
    )
    forge_skills = list(required_stage_contract["workflow_chain"]) or list(intent_config["chains"][complexity])
    if intent in {"REVIEW", "SESSION"}:
        forge_skills = list(intent_config["chains"][complexity])
    execution_mode = choose_execution_mode(args.prompt, intent, complexity, registry)
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
    local_companions = infer_local_companions(
        args.prompt,
        args.repo_signal,
        workspace_router,
        intent,
        complexity,
        registry,
    )
    first_party_companions = match_companions(args.prompt, args.repo_signal)
    runtimes = detect_runtimes(args.repo_signal, registry)
    active_routing_locales = routing_locale_names()
    required_stages = required_stage_contract["required_stages"]
    change_artifacts_required = requires_change_artifacts(intent, complexity, required_stages)
    precheck_required = process_precheck_required(intent, args.prompt, registry)
    baseline_proof_required = baseline_required(intent, complexity)
    verify_change_gate_required = verify_change_required(intent, complexity, required_stages)
    review_state_required = review_artifact_required(intent, complexity, execution_pipeline_key, required_stages)
    durable_process_artifacts_required = change_artifacts_required or any(
        isinstance(item, dict)
        and item.get("status") != "skipped"
        and item.get("stage") in {"brainstorm", "spec-review", "review-pack", "self-review", "quality-gate", "release-doc-sync", "release-readiness", "adoption-check"}
        for item in required_stages
    )
    isolation_recommendation = recommended_isolation_stance(
        intent,
        complexity,
        execution_mode,
        effective_delegation_mode != "controller-baseline",
    )
    baseline_verification = build_baseline_verification(baseline_proof_required, verification)
    worktree_bootstrap = build_worktree_bootstrap(isolation_recommendation)
    review_sequence = build_review_sequence(execution_pipeline_key)
    browser_qa = classify_browser_qa(
        args.prompt,
        intent=intent,
        complexity=complexity,
        domain_skills=domain_skills,
        repo_signals=args.repo_signal,
    )
    packet_mode = classify_packet_mode(
        args.prompt,
        intent=intent,
        complexity=complexity,
        execution_mode=execution_mode,
        execution_pipeline_key=execution_pipeline_key,
        required_stages=required_stages,
        quality_profile_key=quality_profile_key,
    )

    return {
        "prompt": args.prompt,
        "repo_signals": args.repo_signal,
        "workspace_router": str(workspace_router) if workspace_router else None,
        "detected": {
            "intent": intent,
            "complexity": complexity,
            "profile": required_stage_contract["profile"],
            "forge_skills": forge_skills,
            "required_stage_chain": required_stage_contract["required_stage_chain"],
            "required_stages": required_stages,
            "host_skills": host_skills,
            "host_supports_subagents": host_supports_subagents,
            "host_supports_parallel_subagents": host_supports_parallel_subagents,
            "host_capability_tier": host_tier_key,
            "host_dispatch_mode": host_tier.get("dispatch_mode"),
            "resolved_delegation_preference": resolved_delegation_preference,
            "effective_delegation_mode": effective_delegation_mode,
            "domain_skills": domain_skills,
            "first_party_companions": [item["id"] for item in first_party_companions],
            "local_companions": local_companions,
            "runtimes": runtimes,
            "routing_locales": active_routing_locales,
            "verification_profile": verification_key,
            "execution_mode": execution_mode,
            "execution_pipeline": execution_pipeline_key,
            "lane_model_assignments": lane_model_assignments,
            "quality_profile": quality_profile_key,
            "delegation_strategy": delegation_strategy,
            "change_artifacts_required": change_artifacts_required,
            "process_precheck_required": precheck_required,
            "baseline_proof_required": baseline_proof_required,
            "verify_change_required": verify_change_gate_required,
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
            skills=" + ".join([*forge_skills, *host_skills, *domain_skills, *[item["id"] for item in first_party_companions], *local_companions])
            or current_bundle_skill_name(),
        ),
        "registry_source": " + ".join(registry_sources()),
    }


def format_text(report: dict) -> str:
    detected = report["detected"]
    lines = [
        "Forge Route Preview",
        f"- Prompt: {report['prompt']}",
        f"- Intent: {detected['intent']}",
        f"- Complexity: {detected['complexity']}",
        f"- Profile: {detected['profile']}",
        f"- Forge skills: {' -> '.join(detected['forge_skills'])}",
        f"- Required stage chain: {' -> '.join(detected['required_stage_chain']) or '(none)'}",
        f"- Execution mode: {detected['execution_mode'] or '(n/a)'}",
        f"- Execution pipeline: {report['execution_pipeline']['label'] if report['execution_pipeline'] else '(n/a)'}",
        f"- Delegation strategy: {report['delegation_plan']['label'] if report['delegation_plan'] else '(n/a)'}",
        f"- Quality profile: {report['quality_profile']['label']}",
        f"- Host capability tier: {detected['host_capability_tier'] or '(none)'}",
        f"- Host dispatch mode: {detected['host_dispatch_mode'] or '(none)'}",
        f"- Resolved delegation preference: {detected['resolved_delegation_preference'] or '(none)'}",
        f"- Effective delegation mode: {detected['effective_delegation_mode'] or '(none)'}",
        f"- Host skills: {', '.join(detected['host_skills']) or '(none)'}",
        f"- Domain skills: {', '.join(detected['domain_skills']) or '(none)'}",
        f"- First-party companions: {', '.join(detected['first_party_companions']) or '(none)'}",
        f"- Local companions: {', '.join(detected['local_companions']) or '(none)'}",
        f"- Runtimes from repo signals: {', '.join(detected['runtimes']) or '(none)'}",
        f"- Routing locales: {', '.join(detected['routing_locales']) or '(none)'}",
        f"- Verification profile: {report['verification']['label'] if report['verification'] else '(n/a)'}",
        f"- Change artifacts required: {'yes' if detected['change_artifacts_required'] else 'no'}",
        f"- Process precheck required: {'yes' if detected['process_precheck_required'] else 'no'}",
        f"- Baseline proof required: {'yes' if detected['baseline_proof_required'] else 'no'}",
        f"- Verify-change required: {'yes' if detected['verify_change_required'] else 'no'}",
        f"- Review artifact required: {'yes' if detected['review_artifact_required'] else 'no'}",
        f"- Durable process artifacts required: {'yes' if detected['durable_process_artifacts_required'] else 'no'}",
        f"- Isolation recommendation: {detected['isolation_recommendation'] or '(n/a)'}",
        f"- Baseline verification packet: {detected['baseline_verification']['proof_target'] if detected['baseline_verification'] else '(n/a)'}",
        f"- Worktree bootstrap helper: {detected['worktree_bootstrap']['helper'] if detected['worktree_bootstrap'] else '(n/a)'}",
        f"- Browser QA classification: {detected['browser_qa_classification']}",
        f"- Browser QA scope: {', '.join(detected['browser_qa_scope']) or '(none)'}",
        f"- Packet mode: {detected['packet_mode']}",
        f"- Fast lane eligible: {'yes' if detected['fast_lane_eligible'] else 'no'}",
        f"- Assumptions-first mode: {'yes' if detected['assumptions_first_mode'] else 'no'}",
        "- Required stages:",
    ]
    if detected["required_stages"]:
        for item in detected["required_stages"]:
            reason = item.get("activation_reason") or item.get("skip_reason") or "(none)"
            qualifier = f" | mode: {item['mode']}" if item.get("mode") else ""
            lines.append(
                "  - {stage} -> {workflow} | {status} | {reason_type}: {reason}{qualifier}".format(
                    stage=item["stage"],
                    workflow=item["workflow"],
                    status=item["status"],
                    reason_type="activation" if item["status"] != "skipped" else "skip",
                    reason=reason,
                    qualifier=qualifier,
                )
            )
    else:
        lines.append("  - (none)")
    lines.extend([
        "- Lane model tiers:",
    ])
    if detected["lane_model_assignments"]:
        for lane, tier in detected["lane_model_assignments"].items():
            lines.append(f"  - {lane}: {tier}")
    else:
        lines.append("  - (none)")
    if detected["review_sequence"]:
        lines.append("- Review sequence:")
        for item in detected["review_sequence"]:
            review_kind = item["review_kind"] or "implementation"
            dependency = ", ".join(item["depends_on"]) or "none"
            lines.append(f"  - {item['sequence_index']}. {item['lane']} | {review_kind} | depends on: {dependency}")
    if detected["packet_mode_reasons"]:
        lines.append("- Packet mode reasons:")
        for reason in detected["packet_mode_reasons"][:3]:
            lines.append(f"  - {reason}")
    if detected["execution_pipeline"] == "implementer-spec-quality":
        max_revisions = report["execution_pipeline"].get("max_revisions") if report["execution_pipeline"] else None
        if max_revisions is None:
            max_revisions = 3
        lines.append(f"- Spec-review loop cap: {max_revisions}")
    if report["delegation_plan"]:
        lines.append(f"- Delegation summary: {report['delegation_plan']['summary']}")
        lines.append(f"- Delegation dispatch mode: {report['delegation_plan']['dispatch_mode']}")
        lines.append(f"- Delegation host capability tier: {report['delegation_plan'].get('host_capability_tier') or '(none)'}")
        if report["delegation_plan"].get("dispatch_reasons"):
            lines.append("- Delegation dispatch reasons:")
            for reason in report["delegation_plan"]["dispatch_reasons"]:
                lines.append(f"  - {reason}")
        if report["delegation_plan"].get("fallback_reasons"):
            lines.append("- Delegation fallback reasons:")
            for reason in report["delegation_plan"]["fallback_reasons"]:
                lines.append(f"  - {reason}")
        lines.append("- Delegation controller contract:")
        for item in report["delegation_plan"]["controller_contract"]:
            lines.append(f"  - {item}")
        lines.append("- Delegation controller steps:")
        for step in report["delegation_plan"]["controller_steps"]:
            lines.append(f"  - {step}")
        lines.append("- Delegation packet fields:")
        for field in report["delegation_plan"]["packet_template"]["required_fields"]:
            lines.append(f"  - {field}")
        if report["delegation_plan"]["packet_blueprints"]:
            lines.append("- Delegation packet blueprints:")
            for blueprint in report["delegation_plan"]["packet_blueprints"]:
                lines.append(
                    "  - {lane}: {runtime_role} | {scope}".format(
                        lane=blueprint["lane"],
                        runtime_role=blueprint["runtime_role"],
                        scope=blueprint["scope_rule"],
                    )
                )
    lines.extend(["- Quality profile evidence:"])
    for item in report["quality_profile"]["required_evidence"]:
        lines.append(f"  - {item}")
    if report["verification"]:
        lines.extend(["- Verification-first plan:"])
        for step in report["verification"]["steps"]:
            lines.append(f"  - {step}")
    if report["workspace_router"]:
        lines.append(f"- Workspace router: {report['workspace_router']}")
    lines.append(f"- Registry source: {report['registry_source']}")
    lines.append(f"- Activation line: {report['activation_line']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "route-previews")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{slugify(report['prompt'])[:48]}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    record_workflow_event("route-preview", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview Forge routing decisions.")
    parser.add_argument("prompt", help="User prompt or task summary")
    parser.add_argument("--repo-signal", action="append", default=[], help="Repo artifact, path, or signal. Repeatable.")
    parser.add_argument("--workspace-router", type=Path, default=None, help="Optional AGENTS.md or workspace skill map")
    parser.add_argument("--workspace", type=Path, default=None, help="Optional workspace root for preference resolution")
    parser.add_argument("--changed-files", type=int, default=None, help="Optional changed file count to guide complexity")
    parser.add_argument("--has-harness", choices=["auto", "yes", "no"], default="auto", help="Whether a usable test harness is known")
    parser.add_argument(
        "--delegation-preference",
        choices=["off", "auto", "review-lanes", "parallel-workers"],
        default=None,
        help="Optional preview override for resolved delegation preference",
    )
    parser.add_argument("--forge-home", type=Path, default=None, help="Optional Forge state root for preference resolution")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the preview under .forge-artifacts/route-previews")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        print("\nPersisted route preview:")
        print(f"- JSON: {json_path}")
        print(f"- Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
