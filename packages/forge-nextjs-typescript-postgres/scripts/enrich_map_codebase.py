from __future__ import annotations

import argparse
import json
from pathlib import Path

from companion_common import dependency_sets, detected_features


def build_report(workspace: Path) -> dict:
    dependencies, dev_dependencies = dependency_sets(workspace)
    features = detected_features(workspace)
    database_adapters = sorted({"prisma" if {"prisma", "@prisma/client"} & (dependencies | dev_dependencies) else "", "pg" if "pg" in dependencies else "", "drizzle" if {"drizzle-orm", "drizzle-kit"} & (dependencies | dev_dependencies) else ""} - {""})
    auth_markers = [path for path in ("app/(auth)/login/page.tsx", "app/(auth)/signup/page.tsx", "lib/auth/password.ts") if (workspace / path).exists()]
    billing_markers = [path for path in ("app/(app)/billing/page.tsx", "app/api/webhooks/stripe/route.ts", "lib/billing/stripe.ts") if (workspace / path).exists()]
    observability_markers = [path for path in ("app/api/health/route.ts", "app/(app)/status/page.tsx", "lib/observability.ts") if (workspace / path).exists()]
    enrichments = {
        "stack": {
            "companion_family": "nextjs-typescript-postgres",
            "render_surface": "web",
            "database_adapters": database_adapters,
            "frameworks": ["nextjs-app-router"] if (workspace / "app" / "layout.tsx").exists() else [],
            "product_features": sorted(features - {"nextjs", "typescript", "postgres"}),
        },
        "structure": {
            "entrypoints": [
                path for path in ("app/layout.tsx", "app/page.tsx", "prisma/schema.prisma") if (workspace / path).exists()
            ] + auth_markers + billing_markers,
            "integrations": [item for item in ("prisma", "postgres") if item in database_adapters or item == "prisma" and (workspace / "prisma" / "schema.prisma").exists()],
            "risks": [
                "Missing .env.example can hide required deployment env keys."
            ] if not (workspace / ".env.example").exists() else [],
            "open_questions": [] if database_adapters else ["Confirm which Postgres adapter owns migrations and client generation."],
            "next_actions": [
                "Verify lint, typecheck, test, and build before large Next.js changes.",
                "Confirm schema ownership before editing database access paths.",
            ],
            "stack_notes": [
                "App Router markers detected." if (workspace / "app" / "layout.tsx").exists() else "App Router markers are weak.",
                "Prisma schema detected." if (workspace / "prisma" / "schema.prisma").exists() else "No Prisma schema detected.",
            ],
        },
    }
    if auth_markers:
        enrichments["structure"]["integrations"].append("auth")
        enrichments["structure"]["next_actions"].append("Verify signup, login, and session expiry paths before shipping auth changes.")
    if billing_markers:
        enrichments["structure"]["integrations"].append("stripe")
        enrichments["structure"]["next_actions"].append("Verify webhook handling and subscription state transitions before shipping billing changes.")
    if observability_markers:
        enrichments["structure"]["integrations"].extend(["sentry", "opentelemetry"])
        enrichments["structure"]["next_actions"].append("Verify health probes, traces, and release telemetry before declaring deploy readiness.")
        if "observability" not in enrichments["stack"]["product_features"]:
            enrichments["stack"]["product_features"].append("observability")
    return {"status": "PASS", "companion": "nextjs-typescript-postgres", "enrichments": enrichments}


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit map-codebase enrichments for the Next.js TypeScript Postgres companion.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--format", choices=["text", "json"], default="json", help="Output format")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
