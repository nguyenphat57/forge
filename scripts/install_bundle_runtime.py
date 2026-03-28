from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import build_release
from bundle_fingerprint import compute_bundle_fingerprint
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
from package_matrix import resolve_default_install_target
from release_fs import copy_tree, remove_path, sync_tree
from runtime_tool_install_support import apply_runtime_tool_registrations, plan_runtime_tool_registrations


def _resolve_requested_target(
    bundle_name: str,
    target: str | None,
    codex_home: str | None,
    gemini_home: str | None,
) -> str | None:
    if target is not None:
        return target
    default_target = resolve_default_install_target(
        bundle_name,
        codex_home=resolve_codex_home(codex_home),
        gemini_home=resolve_gemini_home(gemini_home),
    )
    return str(default_target) if default_target is not None else None


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
        "bundle_fingerprint": report["bundle_fingerprint"],
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
    if report["codex_runtime_registration"]["enabled"]:
        manifest["codex_runtime_registration"] = report["codex_runtime_registration"]
    if report["gemini_runtime_registration"]["enabled"]:
        manifest["gemini_runtime_registration"] = report["gemini_runtime_registration"]
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
    register_codex_runtime: bool = False,
    register_gemini_runtime: bool = False,
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
    if (register_codex_runtime or register_gemini_runtime) and build_manifest.get("host") != "runtime":
        raise ValueError("Runtime-tool registration is only supported for bundles with host=runtime.")
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
    runtime_registrations = plan_runtime_tool_registrations(
        bundle_name,
        register_codex_runtime=register_codex_runtime,
        codex_home=codex_home,
        register_gemini_runtime=register_gemini_runtime,
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
        "bundle_fingerprint": {
            "source": build_manifest.get("bundle_fingerprint"),
            "installed": None,
            "matches_source": None,
            "host_mutation_expected": activate_codex or activate_gemini,
        },
        "codex_host_activation": codex_host_activation,
        "gemini_host_activation": gemini_host_activation,
        "codex_runtime_registration": runtime_registrations["codex"],
        "gemini_runtime_registration": runtime_registrations["gemini"],
        "state": build_state_metadata(
            bundle_name,
            target_path,
            build_manifest,
            codex_home=codex_home,
            gemini_home=gemini_home,
        ),
    }


def ensure_state_layout(report: dict) -> None:
    state = report.get("state") or {}
    root_value = state.get("root")
    if not isinstance(root_value, str) or not root_value.strip():
        return

    state_root = Path(root_value)
    state_root.mkdir(parents=True, exist_ok=True)

    for key, value in state.items():
        if key == "root" or not isinstance(value, str) or not value.strip():
            continue
        if key.endswith("_path"):
            Path(value).parent.mkdir(parents=True, exist_ok=True)
        elif key.endswith("_dir"):
            Path(value).mkdir(parents=True, exist_ok=True)


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
    apply_runtime_tool_registrations(report)
    installed_fingerprint = compute_bundle_fingerprint(target_path)
    source_fingerprint = report["source_build_manifest"].get("bundle_fingerprint")
    report["bundle_fingerprint"] = {
        "source": source_fingerprint,
        "installed": installed_fingerprint,
        "matches_source": (
            isinstance(source_fingerprint, dict)
            and source_fingerprint.get("sha256") == installed_fingerprint["sha256"]
            and source_fingerprint.get("file_count") == installed_fingerprint["file_count"]
        ),
        "host_mutation_expected": report["codex_host_activation"]["enabled"] or report["gemini_host_activation"]["enabled"],
    }
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
    register_codex_runtime: bool = False,
    register_gemini_runtime: bool = False,
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
        register_codex_runtime=register_codex_runtime,
        register_gemini_runtime=register_gemini_runtime,
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
    if report["codex_runtime_registration"]["enabled"]:
        lines.append("- Codex runtime registration: yes")
        lines.append(f"- Codex runtime registry: {report['codex_runtime_registration']['registry_path']}")
    if report["gemini_runtime_registration"]["enabled"]:
        lines.append("- Gemini runtime registration: yes")
        lines.append(f"- Gemini runtime registry: {report['gemini_runtime_registration']['registry_path']}")
    return "\n".join(lines)
