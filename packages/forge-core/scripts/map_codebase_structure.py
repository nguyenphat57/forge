from __future__ import annotations

import re
from pathlib import Path


ENTRYPOINT_CANDIDATES = (
    "main.py",
    "app.py",
    "manage.py",
    "server.py",
    "src/main.py",
    "src/index.ts",
    "src/main.ts",
    "app/page.tsx",
    "app/layout.tsx",
    "pages/index.tsx",
)
OPERATOR_ENTRYPOINT_CANDIDATES = (
    "scripts/repo_operator.py",
)


def declared_operator_entrypoints(workspace: Path) -> list[str]:
    agents_path = workspace / "AGENTS.md"
    if not agents_path.exists():
        return []

    text = agents_path.read_text(encoding="utf-8")
    matches = re.findall(r"python\s+(scripts/[A-Za-z0-9_.-]+\.py)", text)
    entrypoints: list[str] = []
    seen: set[str] = set()
    for candidate in [*matches, *OPERATOR_ENTRYPOINT_CANDIDATES]:
        normalized = candidate.replace("\\", "/")
        if normalized in seen:
            continue
        if not (workspace / normalized).exists():
            continue
        seen.add(normalized)
        entrypoints.append(normalized)
    return entrypoints


def scan_structure(workspace: Path, stack: dict) -> dict:
    top_level_dirs = sorted(path.name for path in workspace.iterdir() if path.is_dir() and not path.name.startswith("."))
    entrypoints = [candidate for candidate in ENTRYPOINT_CANDIDATES if (workspace / candidate).exists()]
    entrypoints.extend(candidate for candidate in declared_operator_entrypoints(workspace) if candidate not in entrypoints)
    integrations = []
    for marker, label in (
        ("Dockerfile", "docker"),
        ("docker-compose.yml", "docker-compose"),
        (".github/workflows", "github-actions"),
        ("prisma", "prisma"),
        ("alembic.ini", "alembic"),
        (".env.example", "env-example"),
        ("docs", "docs"),
    ):
        if (workspace / marker).exists():
            integrations.append(label)
    testing_paths = [name for name in ("tests", "__tests__", "cypress", "playwright") if (workspace / name).exists()]
    risks = []
    if not (workspace / "README.md").exists():
        risks.append("README is missing, so repo intent may be implicit instead of explicit.")
    if not testing_paths and not stack.get("test_tools"):
        risks.append("No obvious test harness detected.")
    if not entrypoints:
        risks.append("No obvious entrypoint detected from common markers.")
    open_questions = []
    if not stack.get("frameworks"):
        open_questions.append("Framework detection is weak; confirm the primary runtime and app shell.")
    if "github-actions" not in integrations:
        open_questions.append("CI or release automation is not obvious from root markers.")
    next_actions = [
        "Read README, manifests, and detected entrypoints to confirm the primary app shell before editing."
        if entrypoints
        else "Confirm the primary runtime entrypoint or app shell before editing.",
        "Use `help` or `next` to choose the first concrete slice before editing.",
        "Start a change artifact for medium or large work once the slice is clear.",
    ]
    return {
        "top_level_dirs": top_level_dirs,
        "entrypoints": entrypoints,
        "integrations": integrations,
        "testing_paths": testing_paths,
        "risks": risks,
        "open_questions": open_questions,
        "next_actions": next_actions,
    }
