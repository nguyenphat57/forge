from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, timestamp_slug
from companion_matching import match_companions


def _feature_set(matches: list[dict]) -> set[str]:
    features: set[str] = set()
    for item in matches:
        for feature, matched in item.get("features", {}).items():
            if matched:
                features.add(feature)
    return features


def _env_text(workspace: Path) -> str:
    env_path = workspace / ".env.example"
    return env_path.read_text(encoding="utf-8") if env_path.exists() else ""


def _has_any_key(env_text: str, keys: tuple[str, ...]) -> bool:
    return any(key in env_text for key in keys)


def build_report(workspace: Path, profile: str, public_surface: bool | None) -> dict:
    matches = match_companions(workspace=workspace)
    features = _feature_set(matches)
    env_text = _env_text(workspace)
    inferred_public = bool(public_surface) if public_surface is not None else any(feature in features for feature in ("nextjs", "auth", "billing"))
    focus = [
        "Findings first, summary second.",
        "Separate verified behavior from static review gaps.",
        "Close with explicit disposition and branch state.",
    ]
    checklist = [
        "Review changed files with fresh evidence or state that the pass is static-only.",
        "Confirm tests, build, and lane-specific checks were rerun for the current slice.",
        "State disposition: ready-for-merge, changes-required, or blocked-by-residual-risk.",
    ]
    adversarial_checks: list[str] = []
    findings: list[str] = []
    if inferred_public:
        checklist.extend(
            [
                "Check authz, input validation, and secret handling for public-facing routes.",
                "Confirm correct environment, account, and secret scope before release.",
            ]
        )
    if "auth" in features:
        checklist.extend(
            [
                "Verify signup, login, session expiry, and password hashing behavior.",
                "Check access control on every authenticated route touched by the change.",
            ]
        )
        if "AUTH_SECRET" not in env_text:
            findings.append("AUTH_SECRET is not documented in .env.example.")
        if not _has_any_key(env_text, ("APP_URL", "NEXT_PUBLIC_APP_URL", "NEXTAUTH_URL")):
            findings.append("App or callback base URL is not documented in .env.example.")
    if "billing" in features:
        checklist.extend(
            [
                "Verify webhook signature handling, billing access control, and subscription state transitions.",
                "Check for idempotency or duplicate-event handling on payment callbacks.",
            ]
        )
        for key in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
            if key not in env_text:
                findings.append(f"{key} is not documented in .env.example.")
        if not _has_any_key(env_text, ("NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY", "STRIPE_PUBLISHABLE_KEY")):
            findings.append("Stripe publishable key is not documented in .env.example.")
        webhook_paths = (
            workspace / "app" / "api" / "webhooks" / "stripe" / "route.ts",
            workspace / "pages" / "api" / "webhooks" / "stripe.ts",
        )
        if not any(path.exists() for path in webhook_paths):
            findings.append("Stripe webhook route is not obvious in the repo.")
    if "postgres" in features:
        checklist.append("Review migration safety and rollback path for schema changes.")
    if profile == "adversarial":
        adversarial_checks = [
            "Attempt the main flow with missing auth/session state.",
            "Attempt cross-tenant or cross-account access on sensitive endpoints.",
            "Replay webhook or callback events to look for duplicate side effects.",
        ]
    status = "WARN" if findings else "PASS"
    return {
        "status": status,
        "workspace": str(workspace),
        "profile": profile,
        "public_surface": inferred_public,
        "companions": [item["id"] for item in matches],
        "features": sorted(features),
        "review_focus": focus,
        "checklist": checklist,
        "adversarial_checks": adversarial_checks,
        "findings": findings,
        "recommended_follow_ups": ["Document missing env keys before release."] if findings else [],
        "summary": "Review pack is ready." if status == "PASS" else "Review pack found release or security follow-up.",
    }


def persist_report(report: dict, output_dir: str | None) -> dict[str, str]:
    artifact_dir = default_artifact_dir(output_dir, "review-packs")
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
        "Forge Review Pack",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Profile: {report['profile']}",
        f"- Public surface: {'yes' if report['public_surface'] else 'no'}",
        f"- Companions: {', '.join(report['companions']) or '(none)'}",
        f"- Features: {', '.join(report['features']) or '(none)'}",
        f"- Summary: {report['summary']}",
        "- Review focus:",
    ]
    for item in report["review_focus"]:
        lines.append(f"  - {item}")
    lines.append("- Checklist:")
    for item in report["checklist"]:
        lines.append(f"  - {item}")
    if report["adversarial_checks"]:
        lines.append("- Adversarial checks:")
        for item in report["adversarial_checks"]:
            lines.append(f"  - {item}")
    if report["findings"]:
        lines.append("- Findings:")
        for item in report["findings"]:
            lines.append(f"  - {item}")
        lines.append("- Recommended follow-ups:")
        for item in report["recommended_follow_ups"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Findings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Create a lane-aware solo-dev review pack for release-oriented work.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--profile", choices=["standard", "adversarial"], default="standard", help="Review pack profile")
    parser.add_argument("--public", dest="public_surface", action="store_true", help="Force public-surface checks on")
    parser.add_argument("--no-public", dest="public_surface", action="store_false", help="Force public-surface checks off")
    parser.set_defaults(public_surface=None)
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist review pack artifact")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve(), args.profile, args.public_surface)
    if args.persist:
        report["artifacts"] = persist_report(report, args.output_dir or str(args.workspace.resolve()))

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
