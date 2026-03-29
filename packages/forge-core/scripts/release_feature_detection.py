from __future__ import annotations

from pathlib import Path

from workspace_signals import has_any_path, load_package_json, package_dependency_names, read_env_example


def companion_feature_set(matches: list[dict]) -> set[str]:
    features: set[str] = set()
    for item in matches:
        for feature, matched in item.get("features", {}).items():
            if matched:
                features.add(str(feature))
    return features


def detect_release_features(workspace: Path, companion_features: set[str] | None = None) -> tuple[set[str], bool]:
    features = set(companion_features or set())
    package_json = load_package_json(workspace)
    package_names = package_dependency_names(package_json)
    env_text = read_env_example(workspace)

    auth_markers = (
        has_any_path(workspace, "app/(auth)", "lib/auth", "src/auth", "auth.config.ts", "middleware.ts")
        or "AUTH_SECRET" in env_text
        or bool(package_names & {"next-auth", "bcrypt", "bcryptjs", "passlib", "jose"})
    )
    billing_markers = (
        has_any_path(workspace, "app/api/webhooks/stripe", "pages/api/webhooks/stripe.ts", "lib/billing", "src/billing")
        or "STRIPE_SECRET_KEY" in env_text
        or "STRIPE_WEBHOOK_SECRET" in env_text
        or "stripe" in package_names
    )
    postgres_markers = (
        has_any_path(workspace, "prisma/schema.prisma", "alembic.ini", "migrations", "supabase/migrations")
        or "DATABASE_URL" in env_text
        or bool(package_names & {"@prisma/client", "prisma", "pg", "psycopg", "psycopg2"})
    )
    public_surface = (
        has_any_path(workspace, "app", "pages", "api", "frontend", "client", "components")
        or bool(package_names & {"next", "react", "vite", "fastapi", "flask", "django"})
        or auth_markers
        or billing_markers
    )

    if auth_markers:
        features.add("auth")
    if billing_markers:
        features.add("billing")
    if postgres_markers:
        features.add("postgres")
    if "next" in package_names:
        features.add("nextjs")

    return features, public_surface


def detect_release_context(workspace: Path, *, matches: list[dict] | None = None, companion_features: set[str] | None = None) -> tuple[set[str], bool]:
    seeded_features = set(companion_features or set())
    if matches:
        seeded_features.update(companion_feature_set(matches))
    return detect_release_features(workspace, seeded_features)
