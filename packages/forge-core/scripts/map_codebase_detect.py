from __future__ import annotations

from pathlib import Path

from workspace_signals import load_package_json, load_pyproject, package_dependency_names


def _package_json_info(workspace: Path, payload: dict) -> dict:
    combined = package_dependency_names(payload)
    frameworks: list[str] = []
    for dependency, framework in (
        ("next", "nextjs"),
        ("react", "react"),
        ("vite", "vite"),
        ("express", "express"),
        ("fastify", "fastify"),
        ("nestjs", "nestjs"),
        ("@nestjs/core", "nestjs"),
        ("prisma", "prisma"),
    ):
        if dependency in combined:
            frameworks.append(framework)
    test_tools = [tool for tool in ("vitest", "jest", "playwright", "cypress") if tool in combined]
    package_managers = [tool for marker, tool in (("package-lock.json", "npm"), ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun")) if (workspace / marker).exists()]
    return {
        "project_name": payload.get("name") or workspace.name,
        "languages": ["typescript" if (workspace / "tsconfig.json").exists() else "javascript"],
        "frameworks": frameworks,
        "package_managers": package_managers or ["npm"],
        "test_tools": test_tools,
        "manifests": [str(workspace / "package.json")],
    }


def _pyproject_info(workspace: Path, payload: dict) -> dict:
    project = payload.get("project", {}) if isinstance(payload, dict) else {}
    dependencies = list(project.get("dependencies", [])) if isinstance(project, dict) else []
    optional = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
    if isinstance(optional, dict):
        for group_values in optional.values():
            if isinstance(group_values, list):
                dependencies.extend(group_values)
    dependency_text = " ".join(dependencies).lower()
    frameworks = [name for marker, name in (("fastapi", "fastapi"), ("django", "django"), ("flask", "flask"), ("sqlalchemy", "sqlalchemy")) if marker in dependency_text]
    test_tools = [name for marker, name in (("pytest", "pytest"), ("coverage", "coverage")) if marker in dependency_text]
    return {
        "project_name": project.get("name") or workspace.name,
        "languages": ["python"],
        "frameworks": frameworks,
        "package_managers": ["pip"],
        "test_tools": test_tools,
        "manifests": [str(workspace / "pyproject.toml")],
    }


def detect_stack(workspace: Path) -> dict:
    package_json = load_package_json(workspace)
    if package_json:
        return _package_json_info(workspace, package_json)
    pyproject = load_pyproject(workspace)
    if pyproject:
        return _pyproject_info(workspace, pyproject)
    languages: list[str] = []
    if any(workspace.rglob("*.py")):
        languages.append("python")
    if any(workspace.rglob("*.ts")) or any(workspace.rglob("*.tsx")):
        languages.append("typescript")
    if any(workspace.rglob("*.js")) or any(workspace.rglob("*.jsx")):
        languages.append("javascript")
    return {
        "project_name": workspace.name,
        "languages": languages or ["unknown"],
        "frameworks": [],
        "package_managers": [],
        "test_tools": [],
        "manifests": [],
    }
