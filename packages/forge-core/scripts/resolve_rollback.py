from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio


def recommend_strategy(scope: str, impact: str, data_risk: str, has_artifact: bool) -> tuple[str, str, str, list[str]]:
    warnings: list[str] = []

    if scope == "migration":
        warnings.append("Do not blindly roll back a migration when data loss is possible.")
        if data_risk in {"possible", "high"}:
            return (
                "stabilize-before-rollback",
                "review",
                "Pause writes, inspect data impact, and only choose rollback or fix-forward after the data path is clear.",
                warnings,
            )
        return (
            "controlled-migration-rollback",
            "deploy",
            "Use the migration rollback path only after confirming the data shape is reversible and backups are intact.",
            warnings,
        )

    if scope == "deploy":
        if has_artifact and impact in {"broad", "critical"}:
            return (
                "rollback-last-known-good-release",
                "deploy",
                "Return traffic to the last known good release first, then debug the broken release off the hot path.",
                warnings,
            )
        return (
            "fix-forward-or-partial-rollback",
            "debug",
            "Contain the blast radius, compare the failed release against the previous healthy one, and pick the smallest safe rollback surface.",
            warnings,
        )

    if scope == "config":
        return (
            "restore-last-known-good-config",
            "deploy",
            "Restore the last known good configuration or secret set, then rerun post-change verification.",
            warnings,
        )

    if scope == "code-change":
        if impact in {"broad", "critical"}:
            return (
                "revert-change-set",
                "review",
                "Revert the offending change set or disable the feature flag, then verify the user-facing flow is stable.",
                warnings,
            )
        return (
            "targeted-revert",
            "debug",
            "Revert only the narrow failing slice, then re-run the failing verification before broader release actions.",
            warnings,
        )

    raise ValueError(f"Unsupported rollback scope: {scope}")


def build_report(args: argparse.Namespace) -> dict:
    strategy, workflow, action, warnings = recommend_strategy(
        args.scope,
        args.customer_impact,
        args.data_risk,
        args.has_rollback_artifact,
    )
    if args.failure_signal:
        warnings = warnings + [f"Anchor decisions to the observed failure signal: {args.failure_signal}"]

    risk_level = "high" if args.customer_impact in {"broad", "critical"} or args.data_risk in {"possible", "high"} else "medium"
    if args.scope == "migration" and args.data_risk == "high":
        risk_level = "critical"

    verification_checklist = [
        "Confirm the failure signal is reproducible or visible in logs.",
        "Verify the exact target environment and identity before changing anything.",
        "Run post-rollback smoke checks on the affected user flow.",
    ]
    if args.scope in {"deploy", "migration"}:
        verification_checklist.append("Confirm rollback or fix-forward path with the latest artifact or migration metadata.")

    status = "WARN" if any("Do not blindly" in warning for warning in warnings) else "PASS"
    return {
        "status": status,
        "scope": args.scope,
        "environment": args.environment,
        "customer_impact": args.customer_impact,
        "data_risk": args.data_risk,
        "has_rollback_artifact": args.has_rollback_artifact,
        "risk_level": risk_level,
        "recommended_strategy": strategy,
        "suggested_workflow": workflow,
        "immediate_action": action,
        "verification_checklist": verification_checklist,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Rollback Guidance",
        f"- Status: {report['status']}",
        f"- Scope: {report['scope']}",
        f"- Environment: {report['environment']}",
        f"- Risk level: {report['risk_level']}",
        f"- Strategy: {report['recommended_strategy']}",
        f"- Suggested workflow: {report['suggested_workflow']}",
        f"- Immediate action: {report['immediate_action']}",
        "- Verification checklist:",
    ]
    for item in report["verification_checklist"]:
        lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Resolve a host-neutral rollback strategy without executing the rollback blindly.")
    parser.add_argument("--scope", choices=["deploy", "config", "migration", "code-change"], required=True, help="Rollback surface")
    parser.add_argument("--environment", default="production", help="Target environment")
    parser.add_argument("--customer-impact", choices=["limited", "broad", "critical"], default="limited", help="Observed customer impact")
    parser.add_argument("--data-risk", choices=["none", "possible", "high"], default="none", help="Data-loss risk")
    parser.add_argument("--has-rollback-artifact", action="store_true", help="Whether a known-good release or revert artifact is ready")
    parser.add_argument("--failure-signal", default=None, help="Short description of the observed failure signal")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Rollback Guidance", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
