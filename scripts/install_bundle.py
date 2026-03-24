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
DEFAULT_INSTALL_TARGETS = {
    "forge-antigravity": Path.home() / ".gemini" / "antigravity" / "skills" / "forge-antigravity",
    "forge-codex": Path.home() / ".codex" / "skills" / "forge-codex",
}


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


def plan_install(
    bundle_name: str,
    *,
    source: str | None = None,
    target: str | None = None,
    build: bool = False,
    backup: bool = True,
    backup_dir: str | None = None,
    dry_run: bool = False,
) -> dict:
    if build:
        build_release.build_all()

    source_path = resolve_bundle_source(bundle_name, source)
    if not source_path.exists():
        raise FileNotFoundError(f"Bundle source does not exist: {source_path}")

    target_path = resolve_install_target(bundle_name, target)
    validate_install_paths(source_path, target_path)
    build_manifest = load_build_manifest(source_path)
    install_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = Path(backup_dir).expanduser().resolve() if backup_dir else DEFAULT_BACKUP_DIR.resolve()
    backup_path = None
    if backup and target_path.exists():
        backup_path = backup_root / f"{bundle_name}-{install_id}"

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
    }
    (target / "INSTALL-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def install_from_plan(report: dict) -> dict:
    if report["dry_run"]:
        return report

    source_path = Path(report["source"])
    target_path = Path(report["target"])
    backup_path = Path(report["backup_path"]) if report["backup_path"] else None

    if backup_path:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target_path, backup_path)

    if target_path.exists():
        shutil.rmtree(target_path)

    shutil.copytree(source_path, target_path)
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
) -> dict:
    report = plan_install(
        bundle_name,
        source=source,
        target=target,
        build=build,
        backup=backup,
        backup_dir=backup_dir,
        dry_run=dry_run,
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
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
