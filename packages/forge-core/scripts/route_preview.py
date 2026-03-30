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
)
from route_execution_advice import (
    build_baseline_verification,
    build_review_sequence,
    build_worktree_bootstrap,
)
from route_process_requirements import (
    recommended_isolation_stance,
    review_artifact_required,
    requires_change_artifacts,
    verify_change_required,
)
from companion_matching import match_companions
from route_local_companions import infer_local_companions, resolve_workspace_router
from route_risk import should_insert_brainstorm, should_insert_spec_review


def build_report(args: argparse.Namespace) -> dict:
    registry = load_registry()
    host_capabilities = registry.get("host_capabilities", {})
    host_supports_subagents = bool(host_capabilities.get("supports_subagents", False))
    intent, intent_config = detect_intent(args.prompt, registry)
    complexity = detect_complexity(args.prompt, args.changed_files, registry)
    workspace_router = resolve_workspace_router(args.workspace_router)
    forge_skills = list(intent_config["chains"][complexity])
    if should_insert_brainstorm(args.prompt, intent, complexity, registry) and "brainstorm" not in forge_skills:
        forge_skills.insert(0, "brainstorm")
    if should_insert_spec_review(args.prompt, args.repo_signal, intent, complexity, registry) and "spec-review" not in forge_skills:
        build_index = forge_skills.index("build") if "build" in forge_skills else len(forge_skills)
        forge_skills.insert(build_index, "spec-review")
    domain_skills = detect_domain_skills(args.prompt, args.repo_signal, intent, complexity, registry)
    verification_key, verification = choose_verification_profile(
        intent,
        args.prompt,
        args.repo_signal,
        registry,
        args.has_harness,
    )
    execution_mode = choose_execution_mode(args.prompt, intent, complexity, registry)
    quality_profile_key, quality_profile = choose_quality_profile(
        args.prompt,
        args.repo_signal,
        intent,
        complexity,
        registry,
    )
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
    change_artifacts_required = requires_change_artifacts(intent, complexity)
    precheck_required = process_precheck_required(intent, args.prompt, registry)
    baseline_proof_required = baseline_required(intent, complexity)
    verify_change_gate_required = verify_change_required(intent, complexity)
    review_state_required = review_artifact_required(intent, complexity, execution_pipeline_key)
    isolation_recommendation = recommended_isolation_stance(
        intent,
        complexity,
        execution_mode,
        host_supports_subagents,
    )
    baseline_verification = build_baseline_verification(baseline_proof_required, verification)
    worktree_bootstrap = build_worktree_bootstrap(isolation_recommendation)
    review_sequence = build_review_sequence(execution_pipeline_key)

    return {
        "prompt": args.prompt,
        "repo_signals": args.repo_signal,
        "workspace_router": str(workspace_router) if workspace_router else None,
        "detected": {
            "intent": intent,
            "complexity": complexity,
            "forge_skills": forge_skills,
            "host_skills": host_skills,
            "host_supports_subagents": host_supports_subagents,
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
            "durable_process_artifacts_required": change_artifacts_required,
            "isolation_recommendation": isolation_recommendation,
            "baseline_verification": baseline_verification,
            "worktree_bootstrap": worktree_bootstrap,
            "review_sequence": review_sequence,
        },
        "verification": verification,
        "execution_pipeline": execution_pipeline,
        "delegation_plan": delegation_plan,
        "quality_profile": quality_profile,
        "activation_line": "Forge: {intent} | {complexity} | Skills: {skills}".format(
            intent=intent,
            complexity=complexity,
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
        f"- Forge skills: {' -> '.join(detected['forge_skills'])}",
        f"- Execution mode: {detected['execution_mode'] or '(n/a)'}",
        f"- Execution pipeline: {report['execution_pipeline']['label'] if report['execution_pipeline'] else '(n/a)'}",
        f"- Delegation strategy: {report['delegation_plan']['label'] if report['delegation_plan'] else '(n/a)'}",
        f"- Quality profile: {report['quality_profile']['label']}",
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
        "- Lane model tiers:",
    ]
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
    if detected["execution_pipeline"] == "implementer-spec-quality":
        max_revisions = report["execution_pipeline"].get("max_revisions") if report["execution_pipeline"] else None
        if max_revisions is None:
            max_revisions = 3
        lines.append(f"- Spec-review loop cap: {max_revisions}")
    if report["delegation_plan"]:
        lines.append(f"- Delegation summary: {report['delegation_plan']['summary']}")
        lines.append(f"- Delegation dispatch mode: {report['delegation_plan']['dispatch_mode']}")
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
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview Forge routing decisions.")
    parser.add_argument("prompt", help="User prompt or task summary")
    parser.add_argument("--repo-signal", action="append", default=[], help="Repo artifact, path, or signal. Repeatable.")
    parser.add_argument("--workspace-router", type=Path, default=None, help="Optional AGENTS.md or workspace skill map")
    parser.add_argument("--changed-files", type=int, default=None, help="Optional changed file count to guide complexity")
    parser.add_argument("--has-harness", choices=["auto", "yes", "no"], default="auto", help="Whether a usable test harness is known")
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
