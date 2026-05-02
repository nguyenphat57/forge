from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from common import configure_stdio, preference_defaults, resolve_forge_home, resolve_global_preferences_path


IGNORED_EXISTING_ENTRIES = {
    ".DS_Store",
    ".brain",
    ".forge-artifacts",
    ".git",
    ".gitattributes",
    ".gitignore",
    ".gitkeep",
}

PLACEHOLDER_NEEDS_INPUT = "[NEEDS INPUT: {}]"
PLACEHOLDER_CONFIRM = "[TO BE CONFIRMED: {}]"
BLUEPRINT_RELATIVE_PATH = Path("references") / "project-docs-blueprint.md"

DEFAULT_DOCS = (
    "AGENTS.md",
    "docs/PRODUCT.md",
    "docs/STACK.md",
)

OPTIONAL_DOCS = (
    "docs/ARCHITECTURE.md",
    "docs/QUALITY.md",
    "docs/SCHEMA.md",
    "docs/OPERATIONS.md",
    "docs/templates/FEATURE_TASK.md",
)

DOC_EQUIVALENTS = {
    "AGENTS.md": (),
    "docs/PRODUCT.md": ("README.md", "docs/README.md", ".forge-artifacts/codebase/summary.md"),
    "docs/STACK.md": (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        ".forge-artifacts/codebase/stack.json",
    ),
    "docs/ARCHITECTURE.md": ("docs/architecture.md", ".forge-artifacts/codebase/architecture.md"),
    "docs/QUALITY.md": ("docs/quality.md", "TESTING.md", ".forge-artifacts/codebase/testing.md"),
    "docs/SCHEMA.md": ("docs/schema.md", "prisma/schema.prisma", "schema.sql"),
    "docs/OPERATIONS.md": ("docs/operations.md", "Dockerfile", "docker-compose.yml", ".github/workflows"),
    "docs/templates/FEATURE_TASK.md": (),
}

MODE_CHOICES = (
    "auto",
    "greenfield",
    "existing-no-docs",
    "existing-with-docs",
    "normalize-existing-docs",
)


@dataclass(frozen=True)
class WorkspaceSignals:
    workspace: Path
    interesting_entries: tuple[str, ...]
    project_name: str
    readme_title: str | None
    readme_summary: str | None
    package_name: str | None
    manifest_paths: tuple[str, ...]
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    package_scripts: tuple[str, ...]
    top_level_dirs: tuple[str, ...]
    top_level_files: tuple[str, ...]
    has_tests: bool
    has_schema: bool
    has_operations: bool
    has_architecture: bool


def _append_unique(values: list[str], item: str) -> None:
    if item and item not in values:
        values.append(item)


def _sorted_unique(values: list[str]) -> list[str]:
    seen: OrderedDict[str, None] = OrderedDict()
    for item in values:
        if item:
            seen.setdefault(item, None)
    return list(seen)


def _placeholder_needs_input(label: str) -> str:
    return PLACEHOLDER_NEEDS_INPUT.format(label)


def _placeholder_confirm(label: str) -> str:
    return PLACEHOLDER_CONFIRM.format(label)


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_readme_summary(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, None
    lines = path.read_text(encoding="utf-8").splitlines()
    title: str | None = None
    paragraphs: list[str] = []
    current_paragraph: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if title is None and line.startswith("# "):
            title = line[2:].strip()
            continue
        if not line:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            continue
        if line.startswith("#"):
            continue
        current_paragraph.append(line)
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph).strip())
    summary = paragraphs[0] if paragraphs else None
    return title, summary


def _list_interesting_entries(workspace: Path) -> list[str]:
    if not workspace.exists():
        return []
    entries: list[str] = []
    for entry in sorted(workspace.iterdir(), key=lambda item: item.name.lower()):
        if entry.name in IGNORED_EXISTING_ENTRIES:
            continue
        if entry.name.startswith(".") and entry.name not in {".github"}:
            continue
        entries.append(entry.name)
    return entries


def _load_workspace_signals(workspace: Path, project_name_override: str | None) -> WorkspaceSignals:
    readme_path = workspace / "README.md"
    package_json = _read_json_if_exists(workspace / "package.json") or {}
    pyproject = _read_json_if_exists(workspace / "pyproject.toml")
    readme_title, readme_summary = _read_readme_summary(readme_path)
    package_name = package_json.get("name") if isinstance(package_json.get("name"), str) else None

    project_name = (
        (project_name_override or "").strip()
        or (readme_title or "").strip()
        or (package_name or "").strip().replace("-", " ").replace("_", " ").title()
        or workspace.name.replace("-", " ").replace("_", " ").title()
    )

    manifest_paths: list[str] = []
    for relative in (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "Pipfile",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "tsconfig.json",
        "next.config.ts",
        "next.config.js",
    ):
        if (workspace / relative).exists():
            manifest_paths.append(relative)

    dependencies = package_json.get("dependencies", {}) if isinstance(package_json.get("dependencies"), dict) else {}
    dev_dependencies = package_json.get("devDependencies", {}) if isinstance(package_json.get("devDependencies"), dict) else {}
    dependency_names = {*(str(key) for key in dependencies), *(str(key) for key in dev_dependencies)}
    scripts = package_json.get("scripts", {}) if isinstance(package_json.get("scripts"), dict) else {}

    languages: list[str] = []
    if package_json:
        _append_unique(languages, "JavaScript/TypeScript")
    if (workspace / "tsconfig.json").exists():
        _append_unique(languages, "TypeScript")
    if (workspace / "requirements.txt").exists() or (workspace / "pyproject.toml").exists():
        _append_unique(languages, "Python")
    if (workspace / "go.mod").exists():
        _append_unique(languages, "Go")
    if (workspace / "Cargo.toml").exists():
        _append_unique(languages, "Rust")
    if (workspace / "pom.xml").exists():
        _append_unique(languages, "JVM")

    frameworks: list[str] = []
    if "next" in dependency_names or (workspace / "next.config.ts").exists() or (workspace / "next.config.js").exists():
        _append_unique(frameworks, "Next.js")
    if "react" in dependency_names:
        _append_unique(frameworks, "React")
    if "vue" in dependency_names:
        _append_unique(frameworks, "Vue")
    if "svelte" in dependency_names:
        _append_unique(frameworks, "Svelte")
    if "express" in dependency_names:
        _append_unique(frameworks, "Express")
    if (workspace / "prisma" / "schema.prisma").exists():
        _append_unique(frameworks, "Prisma")

    top_level_dirs = tuple(
        entry.name
        for entry in sorted(workspace.iterdir(), key=lambda item: item.name.lower())
        if workspace.exists() and entry.is_dir()
    ) if workspace.exists() else ()
    top_level_files = tuple(
        entry.name
        for entry in sorted(workspace.iterdir(), key=lambda item: item.name.lower())
        if workspace.exists() and entry.is_file()
    ) if workspace.exists() else ()

    has_tests = any(
        (workspace / relative).exists()
        for relative in ("tests", "__tests__", "pytest.ini", "vitest.config.ts", "jest.config.js")
    ) or "test" in scripts
    has_schema = any(
        (workspace / relative).exists()
        for relative in ("prisma/schema.prisma", "schema.sql", "migrations", "db")
    )
    has_operations = any(
        (workspace / relative).exists()
        for relative in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".github/workflows", "Procfile")
    )
    has_architecture = any(
        (workspace / relative).exists()
        for relative in ("app", "src", "packages", "services", ".forge-artifacts/codebase/architecture.md")
    )
    return WorkspaceSignals(
        workspace=workspace,
        interesting_entries=tuple(_list_interesting_entries(workspace)),
        project_name=project_name or "Project",
        readme_title=readme_title,
        readme_summary=readme_summary,
        package_name=package_name,
        manifest_paths=tuple(manifest_paths),
        languages=tuple(languages),
        frameworks=tuple(frameworks),
        package_scripts=tuple(sorted(str(key) for key in scripts)),
        top_level_dirs=top_level_dirs,
        top_level_files=top_level_files,
        has_tests=has_tests,
        has_schema=has_schema,
        has_operations=has_operations,
        has_architecture=has_architecture,
    )


def _resolve_blueprint_path() -> Path:
    script_path = Path(__file__).resolve()
    bundle_root = script_path.parents[1]
    candidates = (
        bundle_root / BLUEPRINT_RELATIVE_PATH,
        bundle_root.parent / "forge-init" / BLUEPRINT_RELATIVE_PATH,
        bundle_root.parent / "forge-skills" / "init" / BLUEPRINT_RELATIVE_PATH,
        script_path.parents[2] / "forge-skills" / "init" / BLUEPRINT_RELATIVE_PATH,
        script_path.parents[3] / "packages" / "forge-skills" / "init" / BLUEPRINT_RELATIVE_PATH,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Missing forge-init blueprint canonical reference. Expected "
        "`forge-init/references/project-docs-blueprint.md` next to the bundle or source tree."
    )


def _canonical_doc_exists(workspace: Path, relative_path: str) -> bool:
    return (workspace / relative_path).exists()


def _equivalent_doc_paths(workspace: Path, relative_path: str) -> list[str]:
    matches: list[str] = []
    for candidate in DOC_EQUIVALENTS.get(relative_path, ()):
        if (workspace / candidate).exists():
            matches.append(candidate)
    return matches


def detect_workspace_mode(workspace: Path) -> str:
    signals = _load_workspace_signals(workspace.resolve(), None)
    return detect_workspace_mode_from_signals(signals)


def detect_workspace_mode_from_signals(signals: WorkspaceSignals) -> str:
    if not signals.interesting_entries:
        return "greenfield"

    has_default_canonical = all(_canonical_doc_exists(signals.workspace, relative) for relative in DEFAULT_DOCS)
    has_any_canonical = any(
        _canonical_doc_exists(signals.workspace, relative)
        for relative in (*DEFAULT_DOCS, *OPTIONAL_DOCS)
    )
    has_equivalent_docs = any(_equivalent_doc_paths(signals.workspace, relative) for relative in (*DEFAULT_DOCS, *OPTIONAL_DOCS))

    if has_default_canonical:
        return "existing-with-docs"
    if has_any_canonical or has_equivalent_docs:
        return "normalize-existing-docs"
    return "existing-no-docs"


def _format_source_list(sources: list[str], placeholder: str) -> str:
    if not sources:
        return f"- {placeholder}"
    return "\n".join(f"- `{source}`" for source in sources)


def _render_agents_doc(signals: WorkspaceSignals, planned_docs: list[str]) -> tuple[str, list[str]]:
    optional_docs = [relative for relative in planned_docs if relative not in DEFAULT_DOCS and relative != "docs/templates/FEATURE_TASK.md"]
    doc_lines = [f"- `{relative}`" for relative in ("docs/PRODUCT.md", "docs/STACK.md", *optional_docs)]
    if not doc_lines:
        doc_lines = [f"- `{relative}`" for relative in ("docs/PRODUCT.md", "docs/STACK.md")]
    text = "\n".join(
        [
            f"# {signals.project_name} Workspace Entry",
            "",
            "Forge remains the evidence-first execution kernel for this workspace. This file is local augmentation only.",
            "",
            "## Read Order",
            "",
            "1. Keep the global Forge orchestrator rules.",
            "2. Read this `AGENTS.md`.",
            "3. Read the project docs that match the current task:",
            *doc_lines,
            "",
            "## Local Rules",
            "",
            "- Treat bootstrap docs as project knowledge, not execution memory.",
            "- Do not write `.brain/session.json` from bootstrap docs; use `forge-session-management` save or closeout for session continuity.",
            "- Use `.forge-artifacts/workflow-state` for automatic execution state, and `.brain` only for explicit continuity sidecars.",
            "- Do not reintroduce `STATUS.md`, `DECISIONS.md`, or `ERRORS.md` as default memory files.",
            "- Prefer repo truth, tests, schemas, and configs over stale prose.",
            "",
            "## Current Gaps",
            "",
            f"- Primary stakeholders: {_placeholder_needs_input('primary stakeholders')}",
            f"- Repo-specific safety boundaries: {_placeholder_confirm('local constraints beyond Forge global rules')}",
        ]
    )
    return text + "\n", ["primary stakeholders", "local constraints beyond Forge global rules"]


def _render_product_doc(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    summary = signals.readme_summary or _placeholder_confirm("project summary from an authoritative source")
    text = "\n".join(
        [
            f"# {signals.project_name} Product",
            "",
            "## Snapshot",
            "",
            f"- Project name: `{signals.project_name}`",
            "- Seed sources:",
            _format_source_list(source_paths, _placeholder_confirm("authoritative product description")),
            f"- Current summary: {summary}",
            "",
            "## Users",
            "",
            f"- Primary users: {_placeholder_needs_input('primary users')}",
            f"- Internal operators: {_placeholder_confirm('internal operators or support teams')}",
            "",
            "## Problem",
            "",
            _placeholder_needs_input("problem statement and why it matters"),
            "",
            "## Goals",
            "",
            f"- {_placeholder_confirm('main user outcome this product must deliver')}",
            f"- {_placeholder_confirm('success metric or observable outcome')}",
            "",
            "## Non-Goals",
            "",
            f"- {_placeholder_confirm('what this project should explicitly not optimize for yet')}",
            "",
            "## Open Questions",
            "",
            f"- {_placeholder_needs_input('scope boundaries and stakeholder priorities')}",
        ]
    )
    return text + "\n", [
        "primary users",
        "problem statement and why it matters",
        "scope boundaries and stakeholder priorities",
    ]


def _render_stack_doc(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    languages = ", ".join(signals.languages) if signals.languages else _placeholder_confirm("primary implementation languages")
    frameworks = ", ".join(signals.frameworks) if signals.frameworks else _placeholder_confirm("frameworks or major libraries")
    commands = ", ".join(signals.package_scripts) if signals.package_scripts else _placeholder_confirm("build/test/dev commands")
    manifests = ", ".join(signals.manifest_paths) if signals.manifest_paths else _placeholder_confirm("manifest files and toolchain markers")
    text = "\n".join(
        [
            f"# {signals.project_name} Stack",
            "",
            "## Current Signals",
            "",
            f"- Languages: {languages}",
            f"- Frameworks: {frameworks}",
            f"- Manifests and toolchain markers: {manifests}",
            "- Seed sources:",
            _format_source_list(source_paths, _placeholder_confirm("runtime and build manifests")),
            "",
            "## Commands",
            "",
            f"- Detected command names: {commands}",
            f"- Canonical dev command: {_placeholder_confirm('development entry command')}",
            f"- Canonical verification command set: {_placeholder_needs_input('lint, typecheck, test, build, or equivalent proof commands')}",
            "",
            "## Runtime Notes",
            "",
            f"- Deployment/runtime expectations: {_placeholder_needs_input('deployment target and runtime environment')}",
            f"- Package manager or environment manager: {_placeholder_confirm('package manager and lockfile policy')}",
        ]
    )
    return text + "\n", [
        "lint, typecheck, test, build, or equivalent proof commands",
        "deployment target and runtime environment",
    ]


def _render_architecture_doc(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    structure = ", ".join(signals.top_level_dirs) if signals.top_level_dirs else _placeholder_confirm("top-level modules and entrypoints")
    text = "\n".join(
        [
            f"# {signals.project_name} Architecture",
            "",
            "## Observed Structure",
            "",
            f"- Top-level directories: {structure}",
            "- Seed sources:",
            _format_source_list(source_paths, _placeholder_confirm("architecture notes or codebase summaries")),
            "",
            "## Boundaries",
            "",
            f"- Core modules and responsibilities: {_placeholder_needs_input('major modules and ownership boundaries')}",
            f"- External integrations: {_placeholder_confirm('services, APIs, or third-party systems')}",
            "",
            "## Open Questions",
            "",
            f"- {_placeholder_needs_input('critical data flow or boundary questions still unresolved')}",
        ]
    )
    return text + "\n", [
        "major modules and ownership boundaries",
        "critical data flow or boundary questions still unresolved",
    ]


def _render_quality_doc(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    test_signal = "present" if signals.has_tests else _placeholder_confirm("test harness not yet identified")
    text = "\n".join(
        [
            f"# {signals.project_name} Quality",
            "",
            "## Current Signals",
            "",
            f"- Existing test signal: {test_signal}",
            f"- Detected script names: {', '.join(signals.package_scripts) if signals.package_scripts else _placeholder_confirm('no command metadata yet')}",
            "- Seed sources:",
            _format_source_list(source_paths, _placeholder_confirm("quality or testing notes")),
            "",
            "## Verification Contract",
            "",
            "- Use the strongest available harness before claiming behavior changes are complete.",
            f"- Required proof sequence for this repo: {_placeholder_needs_input('repo-specific verification order')}",
            "",
            "## Risks",
            "",
            f"- {_placeholder_confirm('areas with weak coverage or brittle verification')}",
        ]
    )
    return text + "\n", ["repo-specific verification order"]


def _render_schema_doc(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    text = "\n".join(
        [
            f"# {signals.project_name} Schema",
            "",
            "## Current Signals",
            "",
            "- Seed sources:",
            _format_source_list(source_paths, _placeholder_confirm("schema files or migration sources")),
            "",
            "## Data Contract",
            "",
            f"- Primary schema owner: {_placeholder_needs_input('schema owner or source of truth')}",
            f"- Key entities or tables: {_placeholder_confirm('core entities, tables, or document types')}",
            "",
            "## Change Safety",
            "",
            f"- Migration and rollback expectations: {_placeholder_needs_input('migration policy and rollback guardrails')}",
        ]
    )
    return text + "\n", ["schema owner or source of truth", "migration policy and rollback guardrails"]


def _render_operations_doc(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    text = "\n".join(
        [
            f"# {signals.project_name} Operations",
            "",
            "## Current Signals",
            "",
            "- Seed sources:",
            _format_source_list(source_paths, _placeholder_confirm("deployment or runtime operations sources")),
            "",
            "## Environments",
            "",
            f"- Environment list: {_placeholder_needs_input('local, staging, production, or other environments')}",
            f"- Secrets and config handling: {_placeholder_confirm('where runtime config is managed')}",
            "",
            "## Operational Checks",
            "",
            f"- Deployment readiness checks: {_placeholder_needs_input('ops smoke checks and rollback triggers')}",
        ]
    )
    return text + "\n", [
        "local, staging, production, or other environments",
        "ops smoke checks and rollback triggers",
    ]


def _render_feature_task_template(signals: WorkspaceSignals, source_paths: list[str]) -> tuple[str, list[str]]:
    del source_paths
    text = "\n".join(
        [
            "# Feature Task",
            "",
            "## Request",
            "",
            _placeholder_needs_input("requested change or feature slice"),
            "",
            "## User Impact",
            "",
            _placeholder_confirm("who benefits and what changes for them"),
            "",
            "## Verification",
            "",
            _placeholder_needs_input("required proof before claiming completion"),
            "",
            "## Open Questions",
            "",
            f"- {_placeholder_needs_input('unknowns that block confident implementation')}",
            "",
            "## Notes",
            "",
            f"- Project context source: `{signals.project_name}` bootstrap docs",
        ]
    )
    return text + "\n", [
        "requested change or feature slice",
        "required proof before claiming completion",
        "unknowns that block confident implementation",
    ]


DOC_RENDERERS = {
    "AGENTS.md": _render_agents_doc,
    "docs/PRODUCT.md": _render_product_doc,
    "docs/STACK.md": _render_stack_doc,
    "docs/ARCHITECTURE.md": _render_architecture_doc,
    "docs/QUALITY.md": _render_quality_doc,
    "docs/SCHEMA.md": _render_schema_doc,
    "docs/OPERATIONS.md": _render_operations_doc,
    "docs/templates/FEATURE_TASK.md": _render_feature_task_template,
}


def _optional_docs_for_mode(signals: WorkspaceSignals, mode: str) -> list[str]:
    docs: list[str] = []
    if signals.has_architecture or _equivalent_doc_paths(signals.workspace, "docs/ARCHITECTURE.md"):
        docs.append("docs/ARCHITECTURE.md")
    if signals.has_tests or _equivalent_doc_paths(signals.workspace, "docs/QUALITY.md"):
        docs.append("docs/QUALITY.md")
    if signals.has_schema or _equivalent_doc_paths(signals.workspace, "docs/SCHEMA.md"):
        docs.append("docs/SCHEMA.md")
    if signals.has_operations or _equivalent_doc_paths(signals.workspace, "docs/OPERATIONS.md"):
        docs.append("docs/OPERATIONS.md")
    if mode != "greenfield":
        docs.append("docs/templates/FEATURE_TASK.md")
    return _sorted_unique(docs)


def _render_doc(relative_path: str, signals: WorkspaceSignals, planned_docs: list[str], source_paths: list[str]) -> tuple[str, list[str]]:
    renderer = DOC_RENDERERS[relative_path]
    if relative_path == "AGENTS.md":
        return renderer(signals, planned_docs)
    return renderer(signals, source_paths)


def _planned_bootstrap_docs(signals: WorkspaceSignals, mode: str) -> list[str]:
    return list(DEFAULT_DOCS) + _optional_docs_for_mode(signals, mode)


def build_plan(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    blueprint_path = _resolve_blueprint_path()
    blueprint_text = blueprint_path.read_text(encoding="utf-8")
    if "Forge Bootstrap Docs Blueprint" not in blueprint_text:
        raise ValueError(f"Unexpected forge-init blueprint content: {blueprint_path}")

    signals = _load_workspace_signals(workspace, args.project_name)
    mode = args.mode if args.mode != "auto" else detect_workspace_mode_from_signals(signals)

    state_root = resolve_forge_home(args.forge_home)
    created_directories: list[str] = []
    created_files: list[str] = []
    normalized_files: list[str] = []
    reused_paths: list[str] = []
    missing_inputs: list[str] = []
    warnings: list[str] = []
    planned_writes: list[tuple[Path, str, str]] = []

    workspace_directories = [
        workspace / "docs",
        workspace / "docs" / "plans",
        workspace / "docs" / "specs",
    ]

    planned_docs = _planned_bootstrap_docs(signals, mode)
    if "docs/templates/FEATURE_TASK.md" in planned_docs:
        workspace_directories.append(workspace / "docs" / "templates")

    if args.apply:
        workspace.mkdir(parents=True, exist_ok=True)

    for directory in workspace_directories:
        if directory.exists():
            _append_unique(reused_paths, str(directory))
            continue
        _append_unique(created_directories, str(directory))
        if args.apply:
            directory.mkdir(parents=True, exist_ok=True)

    for relative_path in planned_docs:
        canonical_path = workspace / relative_path
        source_paths = _equivalent_doc_paths(workspace, relative_path)
        if canonical_path.exists():
            _append_unique(reused_paths, str(canonical_path))
            for source_path in source_paths:
                _append_unique(reused_paths, str(workspace / source_path))
            continue

        content, doc_missing = _render_doc(relative_path, signals, planned_docs, source_paths)
        missing_inputs.extend(doc_missing)
        planned_writes.append((canonical_path, content, "normalize" if source_paths else "create"))
        if source_paths:
            _append_unique(normalized_files, str(canonical_path))
            for source_path in source_paths:
                _append_unique(reused_paths, str(workspace / source_path))
        else:
            _append_unique(created_files, str(canonical_path))

    if args.seed_continuity:
        for path, content in (
            (workspace / ".brain" / "decisions.json", "[]\n"),
            (workspace / ".brain" / "learnings.json", "[]\n"),
        ):
            if path.exists():
                _append_unique(reused_paths, str(path))
                continue
            planned_writes.append((path, content, "create"))
            _append_unique(created_files, str(path))

    if args.seed_preferences:
        preferences_path = resolve_global_preferences_path(args.forge_home)
        if preferences_path.exists():
            _append_unique(reused_paths, str(preferences_path))
        else:
            planned_writes.append(
                (
                    preferences_path,
                    json.dumps(preference_defaults(), indent=2, ensure_ascii=False) + "\n",
                    "create",
                )
            )
            _append_unique(created_files, str(preferences_path))

    if args.apply:
        for path, content, kind in planned_writes:
            if path.exists():
                if kind == "normalize":
                    _append_unique(reused_paths, str(path))
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    recommended_next_workflow = "brainstorm" if mode == "greenfield" else "plan"
    if args.apply:
        recommended_action = (
            "Start with `brainstorm` to lock the project direction on top of the new bootstrap docs."
            if mode == "greenfield"
            else "Start with `plan` against the current repo state and the bootstrap docs now in place."
        )
    else:
        recommended_action = (
            "Review the preview, fill the missing inputs, then run `forge-init` in apply mode before `brainstorm`."
            if mode == "greenfield"
            else "Review reused and normalized docs, then run `forge-init` in apply mode before `plan`."
        )

    return {
        "status": "PASS",
        "workspace": str(workspace),
        "workspace_mode": mode,
        "state_root": str(state_root),
        "forge_home": str(state_root),
        "blueprint_path": str(blueprint_path),
        "applied": args.apply,
        "seed_preferences": args.seed_preferences,
        "seed_continuity": args.seed_continuity,
        "created_directories": _sorted_unique(created_directories),
        "created_files": _sorted_unique(created_files),
        "normalized_files": _sorted_unique(normalized_files),
        "reused_paths": _sorted_unique(reused_paths),
        "missing_inputs": _sorted_unique(missing_inputs),
        "recommended_next_workflow": recommended_next_workflow,
        "recommended_action": recommended_action,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Workspace Bootstrap Engine",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Mode: {report['workspace_mode']}",
        f"- Blueprint: {report['blueprint_path']}",
        f"- State root: {report['state_root']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        f"- Seed preferences: {'yes' if report['seed_preferences'] else 'no'}",
        f"- Seed continuity: {'yes' if report['seed_continuity'] else 'no'}",
        "- Created directories:",
    ]
    if report["created_directories"]:
        for item in report["created_directories"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append("- Created files:")
    if report["created_files"]:
        for item in report["created_files"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append("- Normalized files:")
    if report["normalized_files"]:
        for item in report["normalized_files"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append("- Reused paths:")
    if report["reused_paths"]:
        for item in report["reused_paths"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append("- Missing inputs:")
    if report["missing_inputs"]:
        for item in report["missing_inputs"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append(f"- Next workflow: {report['recommended_next_workflow']}")
    lines.append(f"- Recommended action: {report['recommended_action']}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview or apply the forge-init workspace bootstrap plan.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument(
        "--forge-home",
        type=Path,
        default=None,
        help="Override adapter state root (defaults to $FORGE_HOME, installed adapter state, bundle-native dev state, or ~/.forge only when no bundle-specific fallback exists)",
    )
    parser.add_argument("--project-name", default=None, help="Optional project name used to seed generated docs")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="auto", help="Override workspace classification")
    parser.add_argument("--seed-preferences", action="store_true", help="Also create the adapter-global Forge preferences file with schema defaults")
    parser.add_argument("--seed-continuity", action="store_true", help="Also create empty decisions/learnings continuity files")
    parser.add_argument("--apply", action="store_true", help="Create the planned directories and files")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_plan(args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Workspace Bootstrap Engine", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
