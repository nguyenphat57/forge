from __future__ import annotations

import argparse
import json
from pathlib import Path

import evaluate_canary_readiness
from common import configure_stdio, default_artifact_dir, timestamp_slug
from companion_matching import match_companions
from help_next_support import find_latest_json, read_json_object
from release_profile_contract import (
    PROFILE_RULES,
    stage_required,
    resolve_compatibility_profile,
    resolve_effective_profile,
    resolve_profile_rules,
    resolve_release_tier,
    resolve_release_tier_story,
)
from release_feature_detection import detect_release_context
from workflow_state_support import resolve_workflow_state

def _load_report(path: Path | None, label: str, warnings: list[str]) -> dict | None:
    if path is None:
        return None
    payload = read_json_object(path, label, warnings)
    if isinstance(payload, dict):
        payload["path"] = str(path)
    return payload if isinstance(payload, dict) else None


def _stage_completed(workflow_state: dict | None, stage_name: str) -> bool:
    if not isinstance(workflow_state, dict):
        return False
    stages = workflow_state.get("stages")
    if not isinstance(stages, dict):
        return False
    payload = stages.get(stage_name)
    return isinstance(payload, dict) and payload.get("status") == "completed"


def build_report(workspace: Path, profile: str, canary_dir: Path | None) -> dict:
    matches = match_companions(workspace=workspace)
    features, detected_public_surface = detect_release_context(workspace, matches=matches)
    warnings: list[str] = []
    missing_evidence: list[str] = []
    checks: list[dict] = []
    workflow_state = resolve_workflow_state(workspace, warnings).get("state")
    compatibility_profile = resolve_compatibility_profile(profile, features, workflow_state)
    effective_profile = resolve_effective_profile(
        profile,
        features,
        workflow_state,
        detected_public_surface=detected_public_surface,
    )
    release_tier = resolve_release_tier(effective_profile, compatibility_profile, workflow_state)
    rules = resolve_profile_rules(effective_profile, workflow_state, compatibility_profile=compatibility_profile)
    release_story = resolve_release_tier_story(effective_profile, compatibility_profile, release_tier)
    latest_gate = (workflow_state or {}).get("latest_gate") if isinstance(workflow_state, dict) else None
    latest_adoption_check = (workflow_state or {}).get("latest_adoption_check") if isinstance(workflow_state, dict) else None
    gate_status = "FAIL"
    gate_detail = "No quality gate found."
    if isinstance(latest_gate, dict):
        decision = str(latest_gate.get("decision") or "")
        gate_status = "PASS" if decision == "go" else "WARN" if decision == "conditional" else "FAIL"
        gate_detail = f"{decision}: {latest_gate.get('why') or latest_gate.get('response') or latest_gate.get('label')}"
        if rules["strict_deploy_gate"] and decision == "conditional":
            gate_status = "FAIL"
    checks.append({"id": "quality-gate", "status": gate_status, "detail": gate_detail})

    docs_sync = _load_report(find_latest_json(workspace, ".forge-artifacts/release-doc-sync"), "release-doc-sync", warnings)
    if docs_sync is None:
        docs_status = "FAIL" if rules["require_docs_sync"] else "WARN"
        docs_detail = "No release-doc sync report found."
        if rules["require_docs_sync"]:
            missing_evidence.append("release-doc-sync")
    else:
        docs_status = docs_sync["status"]
        docs_detail = docs_sync.get("summary", docs_sync["status"])
        if rules["require_docs_sync"] and docs_status == "WARN":
            docs_status = "FAIL"
    checks.append({"id": "release-doc-sync", "status": docs_status, "detail": docs_detail})

    workspace_canary = _load_report(find_latest_json(workspace, ".forge-artifacts/workspace-canaries"), "workspace-canary", warnings)
    if workspace_canary is None:
        canary_status = "FAIL" if rules["require_workspace_canary"] else "WARN"
        canary_detail = "No workspace canary report found."
        if rules["require_workspace_canary"]:
            missing_evidence.append("workspace-canary")
    else:
        canary_status = str(workspace_canary.get("status", "warn")).upper()
        canary_detail = workspace_canary.get("summary", "Workspace canary report loaded.")
        if canary_status == "PASS":
            canary_status = "PASS"
        elif canary_status == "WARN" and rules["require_workspace_canary"]:
            canary_status = "FAIL"
    checks.append({"id": "workspace-canary", "status": canary_status, "detail": canary_detail})

    review_pack = _load_report(find_latest_json(workspace, ".forge-artifacts/review-packs"), "review-pack", warnings)
    if review_pack is None:
        review_status = "FAIL" if rules["require_review_pack"] else "WARN"
        review_detail = "No review pack report found."
        if rules["require_review_pack"]:
            missing_evidence.append("review-pack")
    else:
        review_status = review_pack["status"]
        review_detail = review_pack.get("summary", review_pack["status"])
        if rules["require_review_pack"] and review_status == "WARN":
            review_status = "FAIL"
    checks.append({"id": "review-pack", "status": review_status, "detail": review_detail})

    readiness_status = "WARN"
    readiness_detail = "No rollout canary data found."
    readiness_report: dict | None = None
    if canary_dir is not None and canary_dir.exists():
        readiness_report = evaluate_canary_readiness.evaluate_runs(
            evaluate_canary_readiness.load_runs(canary_dir),
            rules["canary_profile"],
        )
        readiness_status = readiness_report["status"]
        readiness_detail = "; ".join(readiness_report["failures"]) if readiness_report["failures"] else "Rollout readiness thresholds passed."
    elif rules["require_rollout_readiness"]:
        readiness_status = "FAIL"
        missing_evidence.append("rollout-readiness")
    checks.append({"id": "rollout-readiness", "status": readiness_status, "detail": readiness_detail})

    release_live = isinstance(latest_adoption_check, dict) or _stage_completed(workflow_state, "deploy")
    if release_live:
        if isinstance(latest_adoption_check, dict):
            impact = str(latest_adoption_check.get("impact") or "neutral")
            confidence = str(latest_adoption_check.get("confidence") or "medium")
            detail = latest_adoption_check.get("label") or latest_adoption_check.get("summary") or "Adoption check recorded."
            friction_categories = latest_adoption_check.get("friction_categories") or []
            release_actions = latest_adoption_check.get("release_actions") or []
            detail = f"{impact} ({confidence} confidence): {detail}"
            if friction_categories:
                detail = f"{detail} | categories: {', '.join(friction_categories)}"
            if release_actions:
                detail = f"{detail} | actions: {', '.join(release_actions)}"
            adoption_status = {"supports": "PASS", "neutral": "WARN", "contradicts": "FAIL"}.get(impact, "WARN")
        else:
            adoption_status = "WARN"
            detail = "Release appears live but no adoption-check signal is recorded yet."
            missing_evidence.append("adoption-check")
        checks.append({"id": "adoption-check", "status": adoption_status, "detail": detail})
    else:
        adoption_status = None

    follow_up_packet = dict(release_story["follow_up_packet"])
    if not release_live:
        follow_up_packet["status"] = "planned"
        follow_up_packet["recorded_actions"] = []
        follow_up_packet["friction_categories"] = []
    elif isinstance(latest_adoption_check, dict):
        follow_up_packet["status"] = {"PASS": "supported", "WARN": "monitoring", "FAIL": "needs-attention"}.get(
            adoption_status or "WARN",
            "monitoring",
        )
        follow_up_packet["recorded_actions"] = latest_adoption_check.get("release_actions") or latest_adoption_check.get(
            "next_actions"
        ) or []
        follow_up_packet["friction_categories"] = latest_adoption_check.get("friction_categories") or []
    else:
        follow_up_packet["status"] = "pending-adoption"
        follow_up_packet["recorded_actions"] = []
        follow_up_packet["friction_categories"] = []

    blockers = [item["detail"] for item in checks if item["status"] == "FAIL"]
    warns = [item["detail"] for item in checks if item["status"] == "WARN"]
    status = "FAIL" if blockers else "WARN" if warns else "PASS"
    return {
        "status": status,
        "workspace": str(workspace),
        "profile": profile,
        "effective_profile": effective_profile,
        "compatibility_profile": compatibility_profile,
        "release_tier": release_tier,
        "features": sorted(features),
        "checks": checks,
        "warnings": warnings + warns,
        "blockers": blockers,
        "missing_evidence": missing_evidence,
        "quality_gate": latest_gate,
        "release_doc_sync": docs_sync,
        "workspace_canary": workspace_canary,
        "review_pack": review_pack,
        "rollout_readiness": readiness_report,
        "adoption_check": latest_adoption_check,
        "release_story": release_story,
        "migration_guidance": release_story["migration_guidance"],
        "rollback_guidance": release_story["rollback_guidance"],
        "follow_up_packet": follow_up_packet,
        "summary": "Core release contract looks ready." if status == "PASS" else "Release readiness still has unresolved gaps.",
    }


def persist_report(report: dict, output_dir: str | None) -> dict[str, str]:
    artifact_dir = default_artifact_dir(output_dir, "release-readiness")
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stamp = timestamp_slug()
    latest_json = artifact_dir / "latest.json"
    history_json = history_dir / f"{stamp}.json"
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    latest_json.write_text(payload, encoding="utf-8")
    history_json.write_text(payload, encoding="utf-8")
    return {"json": str(latest_json)}


def format_text(report: dict) -> str:
    lines = [
        "Forge Release Readiness",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Profile: {report['profile']}",
        f"- Effective profile: {report['effective_profile']}",
        f"- Compatibility profile: {report.get('compatibility_profile') or '(none)'}",
        f"- Release tier: {report['release_tier']}",
        f"- Tier summary: {report['release_story']['summary']}",
        f"- Features: {', '.join(report['features']) or '(none)'}",
        f"- Summary: {report['summary']}",
        "- Checks:",
    ]
    for item in report["checks"]:
        lines.append(f"  - [{item['status']}] {item['id']}: {item['detail']}")
    if report["blockers"]:
        lines.append("- Blockers:")
        for item in report["blockers"]:
            lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    if report["missing_evidence"]:
        lines.append("- Missing evidence:")
        for item in report["missing_evidence"]:
            lines.append(f"  - {item}")
    lines.append("- Migration guidance:")
    lines.append(f"  - {report['migration_guidance']}")
    lines.append("- Rollback guidance:")
    lines.append(f"  - {report['rollback_guidance']}")
    lines.append("- Follow-up packet:")
    lines.append(f"  - {report['follow_up_packet']['name']} [{report['follow_up_packet']['status']}]")
    lines.append(f"  - Focus: {report['follow_up_packet']['focus']}")
    if report["follow_up_packet"]["recorded_actions"]:
        lines.append(f"  - Recorded actions: {', '.join(report['follow_up_packet']['recorded_actions'])}")
    else:
        lines.append(
            f"  - Default actions: {', '.join(report['follow_up_packet']['default_actions'])}"
        )
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Evaluate release readiness from gates, docs sync, and canary artifacts.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--profile", choices=["auto", *sorted(PROFILE_RULES)], default="standard", help="Readiness profile")
    parser.add_argument(
        "--canary-dir",
        type=Path,
        default=None,
        help="Optional canary-runs artifact directory; defaults to .forge-artifacts/canary-runs under the workspace",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist readiness report")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    canary_dir = args.canary_dir.resolve() if args.canary_dir else (args.workspace.resolve() / ".forge-artifacts" / "canary-runs")
    report = build_report(args.workspace.resolve(), args.profile, canary_dir)
    if args.persist:
        report["artifacts"] = persist_report(report, args.output_dir or str(args.workspace.resolve()))

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
