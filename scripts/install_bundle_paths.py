from __future__ import annotations

import json
from pathlib import Path

import build_release


ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
PACKAGES_DIR = ROOT_DIR / "packages"
DEFAULT_BACKUP_DIR = ROOT_DIR / ".install-backups"
DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_GEMINI_HOME = Path.home() / ".gemini"
DEFAULT_INSTALL_TARGETS = {
    "forge-antigravity": Path.home() / ".gemini" / "antigravity" / "skills" / "forge-antigravity",
    "forge-codex": Path.home() / ".codex" / "skills" / "forge-codex",
}
CODEX_GLOBAL_TEMPLATE = "AGENTS.global.md"
GEMINI_GLOBAL_TEMPLATE = "GEMINI.global.md"
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


def resolve_gemini_home(gemini_home: str | None) -> Path:
    if gemini_home:
        return Path(gemini_home).expanduser().resolve()
    return DEFAULT_GEMINI_HOME.resolve()


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
    repo_root = ROOT_DIR.resolve()
    if target == repo_root or repo_root in target.parents:
        raise ValueError(f"Refusing to install inside the repo tree: {target}")
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


def required_bundle_source_paths(bundle_name: str, source: Path) -> list[Path]:
    paths = [
        source / "BUILD-MANIFEST.json",
        source / "scripts" / "write_preferences.py",
    ]
    if bundle_name == "forge-antigravity":
        paths.append(source / GEMINI_GLOBAL_TEMPLATE)
    if bundle_name == "forge-codex":
        paths.append(source / CODEX_GLOBAL_TEMPLATE)
    return paths


def ensure_bundle_source_ready(bundle_name: str, source: Path) -> None:
    missing = [path for path in required_bundle_source_paths(bundle_name, source) if not path.exists()]
    if not missing:
        return

    if source == (DIST_DIR / bundle_name).resolve():
        build_release.build_all()
        missing = [path for path in required_bundle_source_paths(bundle_name, source) if not path.exists()]

    if missing:
        raise FileNotFoundError(f"Missing build artifacts in bundle source: {missing[0]}")
