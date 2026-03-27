from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import build_release
from install_bundle_host import (
    apply_codex_host_activation,
    apply_gemini_host_activation,
    plan_codex_host_activation,
    plan_gemini_host_activation,
)
from install_bundle_paths import (
    DEFAULT_BACKUP_DIR,
    build_state_metadata,
    ensure_bundle_source_ready,
    load_build_manifest,
    resolve_bundle_source,
    resolve_codex_home,
    resolve_gemini_home,
    resolve_install_target,
    validate_install_paths,
)
from release_fs import copy_tree, remove_path, sync_tree


def _resolve_requested_target(
    bundle_name: str,
    target: str | None,
    codex_home: str | None,
    gemini_home: str | None,
) -> str | None:
    if target is not None:
        return target
    if bundle_name == "forge-codex" and codex_home:
        return str(resolve_codex_home(codex_home) / "skills" / "forge-codex")
    if bundle_name == "forge-antigravity" and gemini_home:
        return str(resolve_gemini_home(gemini_home) / "antigravity" / "skills" / "forge-antigravity")
    return None


def write_install_manifest(target: Path, report: dict) -> None:
    manifest = {
        "bundle": report["bundle"],
        "target": report["target"],
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": report["version"],
        "git_revision": report["git_revision"],
        "host": report["host"],
        "source": report["source"],
        "backup_path": report["backup_path"],
        "source_build_manifest": report["source_build_manifest"],
        "state": report["state"],
    }
    if report["codex_host_activation"]["enabled"]:
        activation = report["codex_host_activation"]
        manifest["codex_host_activation"] = {
            "enabled": True,
            "codex_home": activation["codex_home"],
            "agents_path": activation["agents_path"],
            "host_backup_path": activation["host_backup_path"],
        }
    if report["gemini_host_activation"]["enabled"]:
        activation = report["gemini_host_activation"]
        manifest["gemini_host_activation"] = {
            "enabled": True,
            "gemini_home": activation["gemini_home"],
            "gemini_md_path": activation["gemini_md_path"],
            "host_backup_path": activation["host_backup_path"],
        }
    (target / "INSTALL-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def plan_install(
    bundle_name: str,
    *,
    source: str | None = None,
    target: str | None = None,
    build: bool = False,
    backup: bool = True,
    backup_dir: str | None = None,
    dry_run: bool = False,
    activate_codex: bool = False,
    codex_home: str | None = None,
    activate_gemini: bool = False,
    gemini_home: str | None = None,
) -> dict:
    source_path = resolve_bundle_source(bundle_name, source)
    if build:
        build_release.build_all()
    if not source_path.exists():
        raise FileNotFoundError(f"Bundle source does not exist: {source_path}")

    resolved_target = _resolve_requested_target(bundle_name, target, codex_home, gemini_home)
    target_path = resolve_install_target(bundle_name, resolved_target)
    validate_install_paths(source_path, target_path)
    ensure_bundle_source_ready(bundle_name, source_path)

    build_manifest = load_build_manifest(source_path)
    install_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = Path(backup_dir).expanduser().resolve() if backup_dir else DEFAULT_BACKUP_DIR.resolve()
    backup_path = backup_root / f"{bundle_name}-{install_id}" if backup and target_path.exists() else None

    codex_host_activation = plan_codex_host_activation(
        bundle_name=bundle_name,
        source_path=source_path,
        target_path=target_path,
        install_id=install_id,
        backup=backup,
        backup_root=backup_root,
        activate_codex=activate_codex,
        codex_home=codex_home,
    )
    gemini_host_activation = plan_gemini_host_activation(
        bundle_name=bundle_name,
        source_path=source_path,
        target_path=target_path,
        install_id=install_id,
        backup=backup,
        backup_root=backup_root,
        activate_gemini=activate_gemini,
        gemini_home=gemini_home,
    )

    return {
        "bundle": bundle_name,
        "source": str(source_path),
        "target": str(target_path),
        "version": build_manifest.get("version"),
        "git_revision": build_manifest.get("git_revision"),
        "host": build_manifest.get("host"),
        "build_requested": build,
        "dry_run": dry_run,
        "backup_enabled": backup,
        "backup_path": str(backup_path) if backup_path else None,
        "source_build_manifest": build_manifest,
        "codex_host_activation": codex_host_activation,
        "gemini_host_activation": gemini_host_activation,
        "state": build_state_metadata(target_path),
    }


def ensure_state_layout(report: dict) -> None:
    state = report.get("state") or {}
    root_value = state.get("root")
    preferences_value = state.get("preferences_path")
    if not isinstance(root_value, str) or not root_value.strip():
        return

    state_root = Path(root_value)
    state_root.mkdir(parents=True, exist_ok=True)

    if isinstance(preferences_value, str) and preferences_value.strip():
        Path(preferences_value).parent.mkdir(parents=True, exist_ok=True)


def install_from_plan(report: dict) -> dict:
    if report["dry_run"]:
        return report

    source_path = Path(report["source"])
    target_path = Path(report["target"])
    backup_path = Path(report["backup_path"]) if report["backup_path"] else None

    if backup_path:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        copy_tree(target_path, backup_path)

    if target_path.exists() and not target_path.is_dir():
        remove_path(target_path)

    sync_tree(source_path, target_path)
    ensure_state_layout(report)
    apply_codex_host_activation(report)
    apply_gemini_host_activation(report)
    write_install_manifest(target_path, report)
    return report


def install_bundle(
    bundle_name: str,
    *,
    source: str | None = None,
    target: str | None = None,
    build: bool = False,
    backup: bool = True,
    backup_dir: str | None = None,
    dry_run: bool = False,
    activate_codex: bool = False,
    codex_home: str | None = None,
    activate_gemini: bool = False,
    gemini_home: str | None = None,
) -> dict:
    report = plan_install(
        bundle_name,
        source=source,
        target=target,
        build=build,
        backup=backup,
        backup_dir=backup_dir,
        dry_run=dry_run,
        activate_codex=activate_codex,
        codex_home=codex_home,
        activate_gemini=activate_gemini,
        gemini_home=gemini_home,
    )
    return install_from_plan(report)


def format_text(report: dict) -> str:
    lines = [f"Forge Install ({report['bundle']})"]
    lines.append(f"- Version: {report['version']}")
    lines.append(f"- Host: {report['host']}")
    lines.append(f"- Source: {report['source']}")
    lines.append(f"- Target: {report['target']}")
    lines.append(f"- Dry run: {'yes' if report['dry_run'] else 'no'}")
    if report["backup_enabled"]:
        lines.append(f"- Backup: {report['backup_path'] or '(not needed)'}")
    if report["codex_host_activation"]["enabled"]:
        activation = report["codex_host_activation"]
        lines.append("- Codex host activation: yes")
        lines.append(f"- Codex home: {activation['codex_home']}")
        lines.append(f"- Global AGENTS: {activation['agents_path']}")
        lines.append(f"- Retire legacy runtime: {activation['legacy_runtime_path']}")
        if activation["legacy_skill_paths"]:
            lines.append(f"- Retire legacy skills: {', '.join(activation['legacy_skill_paths'])}")
        lines.append(f"- Host backup: {activation['host_backup_path'] or '(not needed)'}")
    if report["gemini_host_activation"]["enabled"]:
        activation = report["gemini_host_activation"]
        lines.append("- Gemini host activation: yes")
        lines.append(f"- Gemini home: {activation['gemini_home']}")
        lines.append(f"- Global GEMINI: {activation['gemini_md_path']}")
        lines.append(f"- Host backup: {activation['host_backup_path'] or '(not needed)'}")
    return "\n".join(lines)
