from __future__ import annotations

import json
from pathlib import Path

from common import default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


def format_text(report: dict) -> str:
    detected = report["detected"]
    lines = [
        "Forge Route Preview",
        f"- Prompt: {report['prompt']}",
        f"- Intent: {detected['intent']}",
        f"- Session mode: {detected['session_mode'] or '(n/a)'}",
        f"- Complexity: {detected['complexity']}",
        f"- Profile: {detected['profile']}",
        f"- Forge skills: {' -> '.join(detected['forge_skills'])}",
        "- Skill selection rationale:",
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
        f"- First-party companions: {', '.join(detected['first_party_companions']) or '(none)'}",
        f"- Local companions: {', '.join(detected['local_companions']) or '(none)'}",
        f"- Runtimes from repo signals: {', '.join(detected['runtimes']) or '(none)'}",
        f"- Routing locales: {', '.join(detected['routing_locales']) or '(none)'}",
        f"- Verification profile: {report['verification']['label'] if report['verification'] else '(n/a)'}",
        f"- Process precheck required: {'yes' if detected['process_precheck_required'] else 'no'}",
        f"- Baseline proof required: {'yes' if detected['baseline_proof_required'] else 'no'}",
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
    if detected["skill_selection_rationale"]:
        for item in detected["skill_selection_rationale"]:
            lines.append(
                "  - {skill}: {reason} ({reason_code})".format(
                    skill=item["skill"],
                    reason=item["reason"],
                    reason_code=item["reason_code"],
                )
            )
    else:
        lines.append("  - none: answered directly because no Forge skill added value.")
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
    lines.append("- Lane model tiers:")
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
    lines.append("- Quality profile evidence:")
    for item in report["quality_profile"]["required_evidence"]:
        lines.append(f"  - {item}")
    if report["verification"]:
        lines.append("- Verification-first plan:")
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
