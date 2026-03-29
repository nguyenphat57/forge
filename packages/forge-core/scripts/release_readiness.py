from __future__ import annotations

import argparse
import json
from pathlib import Path

import evaluate_canary_readiness
from common import configure_stdio, default_artifact_dir, timestamp_slug
from companion_matching import match_companions
from help_next_support import find_latest_json, read_json_object
from release_feature_detection import detect_release_context
from workflow_state_support import resolve_workflow_state


PROFILE_RULES = {
    "standard": {
        "require_docs_sync": False,
        "require_workspace_canary": False,
        "require_rollout_readiness": False,
        "canary_profile": "controlled-rollout",
    },
    "production": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": True,
        "require_review_pack": False,
        "canary_profile": "broad",
    },
    "auth": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": False,
        "require_review_pack": True,
        "canary_profile": "controlled-rollout",
    },
    "billing": {
        "require_docs_sync": True,
        "require_workspace_canary": True,
        "require_rollout_readiness": True,
        "require_review_pack": True,
        "canary_profile": "broad",
    },
}

def _load_report(path: Path | None, label: str, warnings: list[str]) -> dict | None:
    if path is None:
        return None
    payload = read_json_object(path, label, warnings)
    if isinstance(payload, dict):
        payload["path"] = str(path)
    return payload if isinstance(payload, dict) else None


def _effective_profile(profile: str, features: set[str]) -> str:
    if profile != "auto":
        return profile
    if "billing" in features:
        return "billing"
    if "auth" in features:
        return "auth"
    return "standard"


def build_report(workspace: Path, profile: str, canary_dir: Path | None) -> dict:
    matches = match_companions(workspace=workspace)
    features, _ = detect_release_context(workspace, matches=matches)
    effective_profile = _effective_profile(profile, features)
    rules = PROFILE_RULES[effective_profile]
    warnings: list[str] = []
    missing_evidence: list[str] = []
    checks: list[dict] = []
    workflow_state = resolve_workflow_state(workspace, warnings).get("state")
    latest_gate = (workflow_state or {}).get("latest_gate") if isinstance(workflow_state, dict) else None
    gate_status = "FAIL"
    gate_detail = "No quality gate found."
    if isinstance(latest_gate, dict):
        decision = str(latest_gate.get("decision") or "")
        gate_status = "PASS" if decision == "go" else "WARN" if decision == "conditional" else "FAIL"
        gate_detail = f"{decision}: {latest_gate.get('why') or latest_gate.get('response') or latest_gate.get('label')}"
        if profile == "production" and decision == "conditional":
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
        if effective_profile in {"production", "auth", "billing"} and docs_status == "WARN":
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
        elif canary_status == "WARN" and effective_profile in {"production", "billing"}:
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
        if effective_profile in {"auth", "billing"} and review_status == "WARN":
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

    blockers = [item["detail"] for item in checks if item["status"] == "FAIL"]
    warns = [item["detail"] for item in checks if item["status"] == "WARN"]
    status = "FAIL" if blockers else "WARN" if warns else "PASS"
    return {
        "status": status,
        "workspace": str(workspace),
        "profile": profile,
        "effective_profile": effective_profile,
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
