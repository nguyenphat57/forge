from __future__ import annotations

import argparse
import json

from package_matrix import bundle_names
from install_bundle_host import (
    apply_codex_host_activation,
    apply_gemini_host_activation,
    backup_codex_host_activation,
    backup_gemini_host_activation,
    copy_path,
    plan_codex_host_activation,
    plan_gemini_host_activation,
    render_antigravity_global_gemini,
    render_codex_global_agents,
)
from install_bundle_paths import (
    CODEX_GLOBAL_TEMPLATE,
    CODEX_LEGACY_SKILL_GLOB,
    DEFAULT_BACKUP_DIR,
    DEFAULT_CODEX_HOME,
    DEFAULT_GEMINI_HOME,
    DEFAULT_INSTALL_TARGETS,
    DIST_DIR,
    GEMINI_GLOBAL_TEMPLATE,
    PACKAGES_DIR,
    ROOT_DIR,
    STATE_PREFERENCES_RELATIVE_PATH,
    STATE_SCOPE,
    build_state_metadata,
    ensure_bundle_source_ready,
    load_build_manifest,
    required_bundle_source_paths,
    resolve_adapter_state_root,
    resolve_bundle_source,
    resolve_codex_home,
    resolve_gemini_home,
    resolve_install_target,
    validate_install_paths,
)
from install_bundle_runtime import (
    ensure_state_layout,
    format_text,
    install_bundle,
    install_from_plan,
    plan_install,
    write_install_manifest,
)


__all__ = [
    "CODEX_GLOBAL_TEMPLATE",
    "CODEX_LEGACY_SKILL_GLOB",
    "DEFAULT_BACKUP_DIR",
    "DEFAULT_CODEX_HOME",
    "DEFAULT_GEMINI_HOME",
    "DEFAULT_INSTALL_TARGETS",
    "DIST_DIR",
    "GEMINI_GLOBAL_TEMPLATE",
    "PACKAGES_DIR",
    "ROOT_DIR",
    "STATE_PREFERENCES_RELATIVE_PATH",
    "STATE_SCOPE",
    "apply_codex_host_activation",
    "apply_gemini_host_activation",
    "backup_codex_host_activation",
    "backup_gemini_host_activation",
    "build_state_metadata",
    "copy_path",
    "ensure_bundle_source_ready",
    "ensure_state_layout",
    "format_text",
    "install_bundle",
    "install_from_plan",
    "load_build_manifest",
    "plan_codex_host_activation",
    "plan_gemini_host_activation",
    "plan_install",
    "render_antigravity_global_gemini",
    "render_codex_global_agents",
    "required_bundle_source_paths",
    "resolve_adapter_state_root",
    "resolve_bundle_source",
    "resolve_codex_home",
    "resolve_gemini_home",
    "resolve_install_target",
    "validate_install_paths",
    "write_install_manifest",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Install a built Forge bundle into a host runtime path.")
    parser.add_argument("bundle", choices=tuple(bundle_names()), help="Bundle name")
    parser.add_argument("--source", help="Override bundle source path (defaults to dist/<bundle>)")
    parser.add_argument("--target", help="Override install target path")
    parser.add_argument("--build", action="store_true", help="Build dist bundles before installing")
    parser.add_argument("--dry-run", action="store_true", help="Print the install plan without modifying files")
    parser.add_argument("--no-backup", action="store_true", help="Do not back up the current target before replacing it")
    parser.add_argument("--backup-dir", help="Override backup root directory")
    parser.add_argument(
        "--activate-codex",
        action="store_true",
        help="For forge-codex: rewrite Codex global AGENTS.md and retire legacy AWF runtime artifacts.",
    )
    parser.add_argument("--codex-home", help="Override Codex home (defaults to ~/.codex)")
    parser.add_argument(
        "--activate-gemini",
        action="store_true",
        help="For forge-antigravity: rewrite Gemini global GEMINI.md from the bundle template.",
    )
    parser.add_argument("--gemini-home", help="Override Gemini home (defaults to ~/.gemini)")
    parser.add_argument("--inspect", action="store_true", help="Inspect the bundle or installed target without changing files.")
    parser.add_argument("--upgrade", action="store_true", help="Treat the run as an explicit upgrade of an existing target.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()
    if args.inspect and args.upgrade:
        parser.error("--inspect and --upgrade cannot be used together.")
    intent = "inspect" if args.inspect else "upgrade" if args.upgrade else "install"

    report = install_bundle(
        args.bundle,
        source=args.source,
        target=args.target,
        build=args.build,
        backup=not args.no_backup,
        backup_dir=args.backup_dir,
        dry_run=args.dry_run,
        activate_codex=args.activate_codex,
        codex_home=args.codex_home,
        activate_gemini=args.activate_gemini,
        gemini_home=args.gemini_home,
        intent=intent,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
