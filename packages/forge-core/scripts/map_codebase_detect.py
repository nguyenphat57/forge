from __future__ import annotations

import json
from pathlib import Path

import tomllib


def _package_json_info(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies", {})
    dev_dependencies = payload.get("devDependencies", {})
    combined = {**dependencies, **dev_dependencies}
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
    package_managers = [tool for marker, tool in (("package-lock.json", "npm"), ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun")) if (path.parent / marker).exists()]
    return {
        "project_name": payload.get("name") or path.parent.name,
        "languages": ["typescript" if (path.parent / "tsconfig.json").exists() else "javascript"],
        "frameworks": frameworks,
        "package_managers": package_managers or ["npm"],
        "test_tools": test_tools,
        "manifests": [str(path)],
    }


def _pyproject_info(path: Path) -> dict:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
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
        "project_name": project.get("name") or path.parent.name,
        "languages": ["python"],
        "frameworks": frameworks,
        "package_managers": ["pip"],
        "test_tools": test_tools,
        "manifests": [str(path)],
    }


def detect_stack(workspace: Path) -> dict:
    package_json = workspace / "package.json"
    pyproject = workspace / "pyproject.toml"
    if package_json.exists():
        return _package_json_info(package_json)
    if pyproject.exists():
        return _pyproject_info(pyproject)
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
