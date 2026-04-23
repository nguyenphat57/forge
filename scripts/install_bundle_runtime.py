from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import build_release
from bundle_fingerprint import compute_bundle_fingerprint, fingerprint_matches
from install_bundle_host import (
    apply_codex_host_activation,
    apply_gemini_host_activation,
    plan_codex_host_activation,
    plan_gemini_host_activation,
)
from install_bundle_paths import (
    build_state_metadata,
    ensure_bundle_source_ready,
    load_build_manifest,
    resolve_bundle_source,
    resolve_codex_home,
    resolve_default_backup_root,
    resolve_gemini_home,
    resolve_install_target,
    validate_install_paths,
)
from install_bundle_report import build_install_transition, format_text, load_install_manifest, write_install_manifest
from package_matrix import bundle_names, resolve_default_install_target, sibling_skill_names
from release_fs import copy_tree, remove_path, sync_tree


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


def _plan_sibling_skills(bundle_name: str, source_path: Path, target_path: Path) -> dict:
    if bundle_name not in {"forge-codex", "forge-antigravity"}:
        return {"enabled": False, "skills": []}

    skills: list[dict[str, object]] = []
    for skill_name in sibling_skill_names():
        source = source_path.parent / skill_name
        target = target_path.parent / skill_name
        skills.append(
            {
                "name": skill_name,
                "source": str(source),
                "target": str(target),
                "source_exists": source.exists(),
                "target_exists": target.exists(),
            }
        )
    return {"enabled": True, "skills": skills}


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
    intent: str = "install",
) -> dict:
    if bundle_name not in bundle_names():
        raise KeyError(f"Unknown bundle in package matrix: {bundle_name}")
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
    source_fingerprint = build_manifest.get("bundle_fingerprint")
    installed_fingerprint = compute_bundle_fingerprint(target_path) if target_path.exists() and target_path.is_dir() else None
    bundle_sync_required = not fingerprint_matches(source_fingerprint, installed_fingerprint)
    install_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        Path(backup_dir).expanduser().resolve()
        if backup_dir
        else resolve_default_backup_root(
            bundle_name,
            target_path,
            build_manifest,
            codex_home=codex_home,
            gemini_home=gemini_home,
        )
    )
    backup_path = (
        backup_root / f"{bundle_name}-{install_id}"
        if backup and target_path.exists() and intent != "inspect" and bundle_sync_required
        else None
    )
    existing_install = load_install_manifest(target_path)
    transition = build_install_transition(
        existing_install,
        current_version=str(build_manifest.get("version") or "unknown"),
        intent=intent,
        bundle_sync_required=bundle_sync_required,
    )

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
    sibling_skills = _plan_sibling_skills(bundle_name, source_path, target_path)

    return {
        "bundle": bundle_name,
        "source": str(source_path),
        "target": str(target_path),
        "version": build_manifest.get("version"),
        "git_revision": build_manifest.get("git_revision"),
        "host": build_manifest.get("host"),
        "mode": intent,
        "build_requested": build,
        "dry_run": dry_run or intent == "inspect",
        "backup_enabled": backup and intent != "inspect" and bundle_sync_required,
        "backup_path": str(backup_path) if backup_path else None,
        "bundle_sync_required": bundle_sync_required,
        "source_build_manifest": build_manifest,
        "transition": transition,
        "bundle_fingerprint": {
            "source": source_fingerprint,
            "installed": installed_fingerprint,
            "matches_source": fingerprint_matches(source_fingerprint, installed_fingerprint),
            "host_mutation_expected": activate_codex or activate_gemini,
        },
        "codex_host_activation": codex_host_activation,
        "gemini_host_activation": gemini_host_activation,
        "sibling_skills": sibling_skills,
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

    if report.get("bundle_sync_required", True) and backup_path:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        copy_tree(target_path, backup_path)

    if report.get("bundle_sync_required", True) and target_path.exists() and not target_path.is_dir():
        remove_path(target_path)

    if report.get("bundle_sync_required", True):
        sync_tree(source_path, target_path)
    sibling_skills = report.get("sibling_skills") or {}
    if sibling_skills.get("enabled"):
        for skill in sibling_skills.get("skills", []):
            source = Path(str(skill["source"]))
            target = Path(str(skill["target"]))
            if not source.exists():
                raise FileNotFoundError(f"Missing Forge sibling skill bundle source: {source}")
            sync_tree(source, target)
    ensure_state_layout(report)
    apply_codex_host_activation(report)
    apply_gemini_host_activation(report)
    installed_fingerprint = compute_bundle_fingerprint(target_path)
    source_fingerprint = report["source_build_manifest"].get("bundle_fingerprint")
    report["bundle_fingerprint"] = {
        "source": source_fingerprint,
        "installed": installed_fingerprint,
        "matches_source": fingerprint_matches(source_fingerprint, installed_fingerprint),
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
    intent: str = "install",
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
        intent=intent,
    )
    if intent == "inspect":
        return report
    return install_from_plan(report)
