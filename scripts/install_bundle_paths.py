from __future__ import annotations

import json
from pathlib import Path

from bundle_fingerprint import bundle_fingerprint_matches_manifest
import build_release
from package_matrix import bundle_package_spec, bundle_required_paths, default_install_targets

ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
PACKAGES_DIR = ROOT_DIR / "packages"
DEFAULT_BACKUP_DIR = ROOT_DIR / ".install-backups"
DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_GEMINI_HOME = Path.home() / ".gemini"
DEFAULT_INSTALL_TARGETS = default_install_targets(
    codex_home=DEFAULT_CODEX_HOME.resolve(),
    gemini_home=DEFAULT_GEMINI_HOME.resolve(),
)
CODEX_GLOBAL_TEMPLATE = str(bundle_package_spec("forge-codex").get("host_global_template") or "AGENTS.global.md")
GEMINI_GLOBAL_TEMPLATE = str(bundle_package_spec("forge-antigravity").get("host_global_template") or "GEMINI.global.md")
CODEX_LEGACY_SKILL_GLOB = "awf-*"
ADAPTER_STATE_SCOPE = "adapter-global"
RUNTIME_STATE_SCOPE = "runtime-tool-global"
STATE_SCOPE = ADAPTER_STATE_SCOPE
STATE_PREFERENCES_RELATIVE_PATH = Path("state") / "preferences.json"
STATE_EXTRA_PREFERENCES_RELATIVE_PATH = Path("state") / "extra_preferences.json"


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


def _resolve_state_root(
    bundle_name: str,
    target_path: Path,
    state_spec: dict | None,
    *,
    codex_home: str | None,
    gemini_home: str | None,
) -> Path:
    if not isinstance(state_spec, dict):
        return resolve_adapter_state_root(target_path)
    dev_root = state_spec.get("dev_root")
    if not isinstance(dev_root, dict):
        return resolve_adapter_state_root(target_path)
    strategy = dev_root.get("strategy")
    path_relative = dev_root.get("path_relative")
    if not isinstance(path_relative, str) or not path_relative.strip():
        return resolve_adapter_state_root(target_path)
    if strategy == "bundle-parent-relative":
        return (target_path.parent / Path(path_relative)).resolve()
    if strategy == "host-home-relative":
        if target_path.parent.name != "skills":
            return resolve_adapter_state_root(target_path)
        env_var = dev_root.get("env_var")
        if env_var == "CODEX_HOME":
            canonical_target = (resolve_codex_home(codex_home) / "skills" / bundle_name).resolve()
            if target_path.resolve() != canonical_target:
                return resolve_adapter_state_root(target_path)
            return (resolve_codex_home(codex_home) / Path(path_relative)).resolve()
        if env_var == "GEMINI_HOME":
            canonical_target = (resolve_gemini_home(gemini_home) / "antigravity" / "skills" / bundle_name).resolve()
            if target_path.resolve() != canonical_target:
                return resolve_adapter_state_root(target_path)
            return (resolve_gemini_home(gemini_home) / Path(path_relative)).resolve()
    return resolve_adapter_state_root(target_path)


def build_state_metadata(
    bundle_name: str,
    target_path: Path,
    build_manifest: dict | None = None,
    *,
    codex_home: str | None = None,
    gemini_home: str | None = None,
) -> dict:
    state_spec = build_manifest.get("state") if isinstance(build_manifest, dict) else None
    state_root = _resolve_state_root(bundle_name, target_path, state_spec, codex_home=codex_home, gemini_home=gemini_home)
    metadata = {
        "scope": (state_spec or {}).get("scope") or ADAPTER_STATE_SCOPE,
        "root": str(state_root),
    }
    relative_fields = 0
    for key, value in (state_spec or {}).items():
        if key in {"scope", "dev_root"} or not isinstance(value, str) or not value.strip():
            continue
        if key.endswith("_relative_path"):
            metadata[key.replace("_relative_path", "_path")] = str((state_root / Path(value)).resolve())
            relative_fields += 1
        elif key.endswith("_relative_dir"):
            metadata[key.replace("_relative_dir", "_dir")] = str((state_root / Path(value)).resolve())
            relative_fields += 1
    if relative_fields == 0:
        metadata["preferences_path"] = str((state_root / STATE_PREFERENCES_RELATIVE_PATH).resolve())
        metadata["extra_preferences_path"] = str((state_root / STATE_EXTRA_PREFERENCES_RELATIVE_PATH).resolve())
    return metadata


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
    return bundle_required_paths(bundle_name, source)


def _bundle_source_integrity_error(bundle_name: str, expected: dict | None, actual: dict[str, object]) -> ValueError:
    expected_sha = expected.get("sha256") if isinstance(expected, dict) else None
    actual_sha = actual["sha256"]
    return ValueError(
        f"Bundle source fingerprint mismatch for {bundle_name}. "
        f"Expected {expected_sha}, got {actual_sha}."
    )


def ensure_bundle_source_ready(bundle_name: str, source: Path) -> None:
    missing = [path for path in required_bundle_source_paths(bundle_name, source) if not path.exists()]
    if not missing:
        manifest = load_build_manifest(source)
        matches, actual_fingerprint, expected_fingerprint = bundle_fingerprint_matches_manifest(source, manifest)
        if matches:
            return
        if source != (DIST_DIR / bundle_name).resolve():
            raise _bundle_source_integrity_error(bundle_name, expected_fingerprint, actual_fingerprint)
    if source == (DIST_DIR / bundle_name).resolve():
        build_release.build_all()
        if not missing:
            manifest = load_build_manifest(source)
            matches, actual_fingerprint, expected_fingerprint = bundle_fingerprint_matches_manifest(source, manifest)
            if not matches:
                raise _bundle_source_integrity_error(bundle_name, expected_fingerprint, actual_fingerprint)
        missing = [path for path in required_bundle_source_paths(bundle_name, source) if not path.exists()]

    if missing:
        raise FileNotFoundError(f"Missing build artifacts in bundle source: {missing[0]}")
