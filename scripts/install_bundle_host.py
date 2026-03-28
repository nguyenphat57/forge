from __future__ import annotations

import re
from pathlib import Path

from install_bundle_paths import (
    CODEX_GLOBAL_TEMPLATE,
    CODEX_LEGACY_SKILL_GLOB,
    GEMINI_GLOBAL_TEMPLATE,
    resolve_adapter_state_root,
    resolve_codex_home,
    resolve_gemini_home,
)
from release_fs import copy_file, copy_tree, remove_path


UNRESOLVED_TEMPLATE_PATTERN = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def _render_paths(target_path: Path) -> dict[str, str]:
    state_root = resolve_adapter_state_root(target_path)
    return {
        "bundle_root": str(target_path),
        "skill_path": str(target_path / "SKILL.md"),
        "workflows_path": str(target_path / "workflows"),
        "state_root": str(state_root),
        "preferences_path": str(state_root / "state" / "preferences.json"),
        "extra_preferences_path": str(state_root / "state" / "extra_preferences.json"),
        "resolver": f"python {target_path / 'scripts' / 'resolve_preferences.py'}",
    }


def _render_template(template_text: str, replacements: dict[str, str]) -> str:
    rendered = template_text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered.rstrip() + "\n"


def _ensure_rendered_template_is_clean(rendered_text: str, label: str) -> None:
    unresolved = sorted(set(UNRESOLVED_TEMPLATE_PATTERN.findall(rendered_text)))
    if unresolved:
        joined = ", ".join(unresolved)
        raise ValueError(f"Unresolved placeholders remain in {label}: {joined}")


def render_codex_global_agents(template_text: str, codex_home: Path, target_path: Path) -> str:
    paths = _render_paths(target_path)
    rendered = _render_template(
        template_text,
        {
            "{{CODEX_HOME}}": str(codex_home),
            "{{FORGE_CODEX_BUNDLE_ROOT}}": paths["bundle_root"],
            "{{FORGE_CODEX_SKILL}}": paths["skill_path"],
            "{{FORGE_CODEX_WORKFLOWS}}": paths["workflows_path"],
            "{{FORGE_CODEX_STATE_ROOT}}": paths["state_root"],
            "{{FORGE_CODEX_PREFERENCES_PATH}}": paths["preferences_path"],
            "{{FORGE_CODEX_EXTRA_PREFERENCES_PATH}}": paths["extra_preferences_path"],
            "{{FORGE_CODEX_RESOLVER}}": paths["resolver"],
        },
    )
    _ensure_rendered_template_is_clean(rendered, "Codex global AGENTS template")
    return rendered


def render_antigravity_global_gemini(template_text: str, gemini_home: Path, target_path: Path) -> str:
    paths = _render_paths(target_path)
    rendered = _render_template(
        template_text,
        {
            "{{GEMINI_HOME}}": str(gemini_home),
            "{{FORGE_ANTIGRAVITY_SKILL}}": paths["skill_path"],
            "{{FORGE_ANTIGRAVITY_BUNDLE_ROOT}}": paths["bundle_root"],
            "{{FORGE_ANTIGRAVITY_WORKFLOWS}}": paths["workflows_path"],
            "{{FORGE_ANTIGRAVITY_STATE_ROOT}}": paths["state_root"],
            "{{FORGE_ANTIGRAVITY_PREFERENCES_PATH}}": paths["preferences_path"],
            "{{FORGE_ANTIGRAVITY_EXTRA_PREFERENCES_PATH}}": paths["extra_preferences_path"],
            "{{FORGE_ANTIGRAVITY_RESOLVER}}": paths["resolver"],
        },
    )
    _ensure_rendered_template_is_clean(rendered, "Antigravity global GEMINI template")
    return rendered


def plan_codex_host_activation(
    *,
    bundle_name: str,
    source_path: Path,
    target_path: Path,
    install_id: str,
    backup: bool,
    backup_root: Path,
    activate_codex: bool,
    codex_home: str | None,
) -> dict:
    if not activate_codex:
        return {"enabled": False}

    if bundle_name != "forge-codex":
        raise ValueError("--activate-codex is only valid for the forge-codex bundle.")

    codex_home_path = resolve_codex_home(codex_home)
    expected_target = (codex_home_path / "skills" / "forge-codex").resolve()
    if target_path != expected_target:
        raise ValueError(
            f"--activate-codex requires target path '{expected_target}'. "
            f"Received '{target_path}'."
        )

    template_path = source_path / CODEX_GLOBAL_TEMPLATE
    if not template_path.exists():
        raise FileNotFoundError(f"Missing {CODEX_GLOBAL_TEMPLATE} in bundle source: {source_path}")

    agents_path = codex_home_path / "AGENTS.md"
    legacy_runtime_path = codex_home_path / "awf-codex"
    skills_root = codex_home_path / "skills"
    legacy_skill_paths = sorted(path.resolve() for path in skills_root.glob(CODEX_LEGACY_SKILL_GLOB) if path.exists())
    host_backup_path = None
    if backup and (agents_path.exists() or legacy_runtime_path.exists() or legacy_skill_paths):
        host_backup_path = backup_root / f"{bundle_name}-host-{install_id}"

    return {
        "enabled": True,
        "codex_home": str(codex_home_path),
        "agents_path": str(agents_path),
        "template_path": str(template_path),
        "legacy_runtime_path": str(legacy_runtime_path),
        "legacy_skill_paths": [str(path) for path in legacy_skill_paths],
        "host_backup_path": str(host_backup_path) if host_backup_path else None,
    }


def plan_gemini_host_activation(
    *,
    bundle_name: str,
    source_path: Path,
    target_path: Path,
    install_id: str,
    backup: bool,
    backup_root: Path,
    activate_gemini: bool,
    gemini_home: str | None,
) -> dict:
    if not activate_gemini:
        return {"enabled": False}

    if bundle_name != "forge-antigravity":
        raise ValueError("--activate-gemini is only valid for the forge-antigravity bundle.")

    gemini_home_path = resolve_gemini_home(gemini_home)
    expected_target = (gemini_home_path / "antigravity" / "skills" / "forge-antigravity").resolve()
    if target_path != expected_target:
        raise ValueError(
            f"--activate-gemini requires target path '{expected_target}'. "
            f"Received '{target_path}'."
        )

    template_path = source_path / GEMINI_GLOBAL_TEMPLATE
    if not template_path.exists():
        raise FileNotFoundError(f"Missing {GEMINI_GLOBAL_TEMPLATE} in bundle source: {source_path}")

    gemini_md_path = gemini_home_path / "GEMINI.md"
    host_backup_path = None
    if backup and gemini_md_path.exists():
        host_backup_path = backup_root / f"{bundle_name}-host-{install_id}"

    return {
        "enabled": True,
        "gemini_home": str(gemini_home_path),
        "gemini_md_path": str(gemini_md_path),
        "template_path": str(template_path),
        "host_backup_path": str(host_backup_path) if host_backup_path else None,
    }


def copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        copy_tree(source, destination)
        return
    copy_file(source, destination)


def backup_codex_host_activation(activation: dict) -> None:
    host_backup_path = activation.get("host_backup_path")
    if not host_backup_path:
        return

    backup_root = Path(host_backup_path)
    backup_root.mkdir(parents=True, exist_ok=True)

    agents_path = Path(activation["agents_path"])
    if agents_path.exists():
        copy_path(agents_path, backup_root / "AGENTS.md")

    legacy_runtime_path = Path(activation["legacy_runtime_path"])
    if legacy_runtime_path.exists():
        copy_path(legacy_runtime_path, backup_root / "awf-codex")

    for raw_path in activation["legacy_skill_paths"]:
        skill_path = Path(raw_path)
        if skill_path.exists():
            copy_path(skill_path, backup_root / "skills" / skill_path.name)


def backup_gemini_host_activation(activation: dict) -> None:
    host_backup_path = activation.get("host_backup_path")
    if not host_backup_path:
        return

    backup_root = Path(host_backup_path)
    backup_root.mkdir(parents=True, exist_ok=True)

    gemini_md_path = Path(activation["gemini_md_path"])
    if gemini_md_path.exists():
        copy_path(gemini_md_path, backup_root / "GEMINI.md")


def apply_codex_host_activation(report: dict) -> None:
    activation = report["codex_host_activation"]
    if not activation["enabled"]:
        return

    backup_codex_host_activation(activation)

    codex_home_path = Path(activation["codex_home"])
    codex_home_path.mkdir(parents=True, exist_ok=True)

    agents_path = Path(activation["agents_path"])
    template_path = Path(activation["template_path"])
    rendered_agents = render_codex_global_agents(
        template_path.read_text(encoding="utf-8"),
        codex_home_path,
        Path(report["target"]),
    )
    if agents_path.exists() and agents_path.is_dir():
        remove_path(agents_path)
    agents_path.parent.mkdir(parents=True, exist_ok=True)
    agents_path.write_text(rendered_agents, encoding="utf-8")

    legacy_runtime_path = Path(activation["legacy_runtime_path"])
    if legacy_runtime_path.exists():
        remove_path(legacy_runtime_path)

    for raw_path in activation["legacy_skill_paths"]:
        skill_path = Path(raw_path)
        if skill_path.exists():
            remove_path(skill_path)


def apply_gemini_host_activation(report: dict) -> None:
    activation = report["gemini_host_activation"]
    if not activation["enabled"]:
        return

    backup_gemini_host_activation(activation)

    gemini_home_path = Path(activation["gemini_home"])
    gemini_home_path.mkdir(parents=True, exist_ok=True)

    gemini_md_path = Path(activation["gemini_md_path"])
    template_path = Path(activation["template_path"])
    rendered_gemini = render_antigravity_global_gemini(
        template_path.read_text(encoding="utf-8"),
        gemini_home_path,
        Path(report["target"]),
    )
    if gemini_md_path.exists() and gemini_md_path.is_dir():
        remove_path(gemini_md_path)
    gemini_md_path.parent.mkdir(parents=True, exist_ok=True)
    gemini_md_path.write_text(rendered_gemini, encoding="utf-8")
