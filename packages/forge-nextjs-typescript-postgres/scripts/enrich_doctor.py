from __future__ import annotations

import argparse
import json
from pathlib import Path

from companion_common import dependency_sets, detected_features, env_example_text


def _check(identifier: str, label: str, status: str, detail: str, remediation: str = "") -> dict:
    return {
        "id": identifier,
        "label": label,
        "category": "companion",
        "status": status,
        "detail": detail,
        "remediation": remediation,
    }


def build_report(workspace: Path) -> dict:
    dependencies, dev_dependencies = dependency_sets(workspace)
    features = detected_features(workspace)
    env_text = env_example_text(workspace)
    checks = [
        _check(
            "nextjs-package",
            "Next.js package",
            "PASS" if "next" in dependencies else "FAIL",
            "Detected `next` dependency." if "next" in dependencies else "Missing `next` dependency.",
            "" if "next" in dependencies else "Add `next` before using the Next.js companion.",
        ),
        _check(
            "typescript-config",
            "TypeScript config",
            "PASS" if (workspace / "tsconfig.json").exists() else "WARN",
            "Found tsconfig.json." if (workspace / "tsconfig.json").exists() else "tsconfig.json is missing.",
            "" if (workspace / "tsconfig.json").exists() else "Add tsconfig.json so the TypeScript lane has a stable compile contract.",
        ),
        _check(
            "app-router-root",
            "App Router root",
            "PASS" if (workspace / "app" / "layout.tsx").exists() else "WARN",
            "Found app/layout.tsx." if (workspace / "app" / "layout.tsx").exists() else "App Router root is not obvious.",
            "" if (workspace / "app" / "layout.tsx").exists() else "Add app/layout.tsx or confirm that this repo is not using App Router.",
        ),
        _check(
            "postgres-adapter",
            "Postgres adapter",
            "PASS" if {"@prisma/client", "pg", "postgres", "drizzle-orm", "kysely"} & dependencies or {"prisma", "drizzle-kit"} & dev_dependencies else "WARN",
            "Detected a Postgres-oriented adapter." if {"@prisma/client", "pg", "postgres", "drizzle-orm", "kysely"} & dependencies or {"prisma", "drizzle-kit"} & dev_dependencies else "No Postgres adapter dependency detected yet.",
            "" if {"@prisma/client", "pg", "postgres", "drizzle-orm", "kysely"} & dependencies or {"prisma", "drizzle-kit"} & dev_dependencies else "Add Prisma, pg, drizzle, or another supported Postgres adapter before claiming this lane is fully wired.",
        ),
        _check(
            "env-example",
            "Environment example",
            "PASS" if (workspace / ".env.example").exists() else "WARN",
            "Found .env.example." if (workspace / ".env.example").exists() else ".env.example is missing.",
            "" if (workspace / ".env.example").exists() else "Add .env.example so required database and app env keys are explicit.",
        ),
    ]
    if "auth" in features:
        checks.append(
            _check(
                "auth-secret",
                "Auth secret",
                "PASS" if "AUTH_SECRET" in env_text else "WARN",
                "AUTH_SECRET is documented in .env.example." if "AUTH_SECRET" in env_text else "AUTH_SECRET is not documented in .env.example.",
                "" if "AUTH_SECRET" in env_text else "Add AUTH_SECRET to .env.example before shipping auth flows.",
            )
        )
    if "billing" in features:
        checks.append(
            _check(
                "stripe-env",
                "Stripe env keys",
                "PASS" if "STRIPE_SECRET_KEY" in env_text and "STRIPE_WEBHOOK_SECRET" in env_text else "WARN",
                "Stripe keys are documented in .env.example." if "STRIPE_SECRET_KEY" in env_text and "STRIPE_WEBHOOK_SECRET" in env_text else "Stripe env keys are incomplete in .env.example.",
                "" if "STRIPE_SECRET_KEY" in env_text and "STRIPE_WEBHOOK_SECRET" in env_text else "Add STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET to .env.example before shipping billing.",
            )
        )
    if "observability" in features:
        checks.append(
            _check(
                "observability-env",
                "Observability env",
                "PASS" if "SENTRY_DSN" in env_text and "OTEL_EXPORTER_OTLP_ENDPOINT" in env_text else "WARN",
                "Observability env keys are documented in .env.example." if "SENTRY_DSN" in env_text and "OTEL_EXPORTER_OTLP_ENDPOINT" in env_text else "Observability env keys are incomplete in .env.example.",
                "" if "SENTRY_DSN" in env_text and "OTEL_EXPORTER_OTLP_ENDPOINT" in env_text else "Add SENTRY_DSN and OTEL_EXPORTER_OTLP_ENDPOINT to .env.example before shipping deploy readiness.",
            )
        )
    return {"status": "PASS", "companion": "nextjs-typescript-postgres", "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit doctor enrichments for the Next.js TypeScript Postgres companion.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--format", choices=["text", "json"], default="json", help="Output format")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
