from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import build_release


ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
PACKAGES_DIR = ROOT_DIR / "packages"
DEFAULT_BACKUP_DIR = ROOT_DIR / ".install-backups"
DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_INSTALL_TARGETS = {
    "forge-antigravity": Path.home() / ".gemini" / "antigravity" / "skills" / "forge-antigravity",
    "forge-codex": Path.home() / ".codex" / "skills" / "forge-codex",
}
CODEX_GLOBAL_TEMPLATE = "AGENTS.global.md"
CODEX_LEGACY_SKILL_GLOB = "awf-*"
STATE_SCOPE = "adapter-global"
STATE_PREFERENCES_RELATIVE_PATH = Path("state") / "preferences.json"


def resolve_bundle_source(bundle_name: str, source: str | None) -> Path:
    if source:
        return Path(source).expanduser().resolve()
    return (DIST_DIR / bundle_name).resolve()


def resolve_install_target(bundle_name: str, target: str | None) -> Path:
    if target:
        return Path(target).expanduser().resolve()
    default_target = DEFAULT_INSTALL_TARGETS.get(bundle_name)
    if default_target is None:
        raise ValueError(f"Bundle '{bundle_name}' does not have a default install target; pass --target explicitly.")
    return default_target.resolve()


def resolve_codex_home(codex_home: str | None) -> Path:
    if codex_home:
        return Path(codex_home).expanduser().resolve()
    return DEFAULT_CODEX_HOME.resolve()


def resolve_adapter_state_root(target_path: Path) -> Path:
    target_path = target_path.resolve()
    if target_path.parent.name == "skills":
        return (target_path.parent.parent / target_path.name).resolve()
    return (target_path.parent / f"{target_path.name}-state").resolve()


def build_state_metadata(target_path: Path) -> dict:
    state_root = resolve_adapter_state_root(target_path)
    return {
        "scope": STATE_SCOPE,
        "root": str(state_root),
        "preferences_path": str(state_root / STATE_PREFERENCES_RELATIVE_PATH),
    }


def validate_install_paths(source: Path, target: Path) -> None:
    source = source.resolve()
    target = target.resolve()
    protected_paths = {ROOT_DIR.resolve(), DIST_DIR.resolve(), PACKAGES_DIR.resolve()}
    if target in protected_paths:
        raise ValueError(f"Refusing to install into protected repo path: {target}")
    if target == Path(target.anchor):
        raise ValueError(f"Refusing to install into filesystem root: {target}")
    if target == source:
        raise ValueError("Source and target cannot be the same path.")
    if source in target.parents or target in source.parents:
        raise ValueError("Source and target cannot contain each other.")


def load_build_manifest(source: Path) -> dict:
    manifest_path = source / "BUILD-MANIFEST.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing BUILD-MANIFEST.json in bundle source: {source}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def render_codex_global_agents(template_text: str, codex_home: Path, target_path: Path) -> str:
    rendered = template_text
    rendered = rendered.replace("{{CODEX_HOME}}", str(codex_home))
    rendered = rendered.replace("{{FORGE_CODEX_SKILL}}", str(target_path))
    rendered = rendered.replace("{{FORGE_CODEX_WORKFLOWS}}", str(target_path / "workflows"))
    return rendered.rstrip() + "\n"


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
) -> dict:
    if build:
        build_release.build_all()

    source_path = resolve_bundle_source(bundle_name, source)
    if not source_path.exists():
        raise FileNotFoundError(f"Bundle source does not exist: {source_path}")

    resolved_target = target
    if bundle_name == "forge-codex" and codex_home and target is None:
        resolved_target = str(resolve_codex_home(codex_home) / "skills" / "forge-codex")

    target_path = resolve_install_target(bundle_name, resolved_target)
    validate_install_paths(source_path, target_path)
    build_manifest = load_build_manifest(source_path)
    install_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = Path(backup_dir).expanduser().resolve() if backup_dir else DEFAULT_BACKUP_DIR.resolve()
    backup_path = None
    if backup and target_path.exists():
        backup_path = backup_root / f"{bundle_name}-{install_id}"
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
    state = build_state_metadata(target_path)

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
        "state": state,
    }


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
    (target / "INSTALL-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def prune_extra_entries(source: Path, target: Path) -> None:
    if not target.exists() or not target.is_dir():
        return

    source_names = {item.name for item in source.iterdir()}
    for child in target.iterdir():
        if child.name in source_names:
            source_child = source / child.name
            if child.is_dir() and source_child.is_dir():
                prune_extra_entries(source_child, child)
            continue
        remove_path(child)


def sync_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    prune_extra_entries(source, target)
    shutil.copytree(source, target, dirs_exist_ok=True)


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
        shutil.copytree(target_path, backup_path)

    if target_path.exists() and not target_path.is_dir():
        target_path.unlink()

    sync_tree(source_path, target_path)
    ensure_state_layout(report)
    apply_codex_host_activation(report)
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
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install a built Forge bundle into a host runtime path.")
    parser.add_argument("bundle", choices=["forge-core", "forge-antigravity", "forge-codex"], help="Bundle name")
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
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

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
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
