from __future__ import annotations

import json
import os
from pathlib import Path


BUNDLE_ROOT_ENV_VAR = "FORGE_COMPANION_BUNDLE_ROOT"


def resolve_bundle_root() -> Path:
    override = os.environ.get(BUNDLE_ROOT_ENV_VAR)
    if isinstance(override, str) and override.strip():
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


ROOT_DIR = resolve_bundle_root()


def read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_capabilities() -> dict:
    return read_json(ROOT_DIR / "data" / "companion-capabilities.json")


def load_command_profiles() -> list[dict]:
    payload = read_json(ROOT_DIR / "data" / "command-profiles.json")
    profiles = payload.get("profiles")
    return profiles if isinstance(profiles, list) else []


def load_verification_packs() -> list[dict]:
    payload = read_json(ROOT_DIR / "data" / "verification-packs.json")
    packs = payload.get("packs")
    return packs if isinstance(packs, list) else []


def load_package_json(workspace: Path) -> dict:
    path = workspace / "package.json"
    if not path.exists():
        return {}
    return read_json(path)


def dependency_sets(workspace: Path) -> tuple[set[str], set[str]]:
    payload = load_package_json(workspace)
    dependencies = payload.get("dependencies")
    dev_dependencies = payload.get("devDependencies")
    return (
        set(dependencies) if isinstance(dependencies, dict) else set(),
        set(dev_dependencies) if isinstance(dev_dependencies, dict) else set(),
    )


def detected_features(workspace: Path) -> set[str]:
    dependencies, dev_dependencies = dependency_sets(workspace)
    features: set[str] = set()
    if "next" in dependencies:
        features.add("nextjs")
    if "typescript" in dependencies or "typescript" in dev_dependencies or (workspace / "tsconfig.json").exists():
        features.add("typescript")
    if {"pg", "postgres", "@prisma/client", "drizzle-orm", "kysely"} & dependencies or {"prisma", "drizzle-kit"} & dev_dependencies or (workspace / "prisma" / "schema.prisma").exists():
        features.add("postgres")
    if {"bcryptjs", "zod"} & dependencies or (workspace / "lib" / "auth").exists() or (workspace / "app" / "(auth)").exists():
        features.add("auth")
    if "stripe" in dependencies or (workspace / "lib" / "billing").exists() or (workspace / "app" / "api" / "webhooks" / "stripe" / "route.ts").exists():
        features.add("billing")
    if "@sentry/nextjs" in dependencies or "@opentelemetry/api" in dependencies or (workspace / "lib" / "observability.ts").exists() or (workspace / "app" / "api" / "health" / "route.ts").exists() or (workspace / "app" / "(app)" / "status" / "page.tsx").exists():
        features.add("observability")
    return features


def env_example_text(workspace: Path) -> str:
    path = workspace / ".env.example"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def package_manager(workspace: Path) -> str:
    for marker, name in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("package-lock.json", "npm"),
    ):
        if (workspace / marker).exists():
            return name
    return "npm"
