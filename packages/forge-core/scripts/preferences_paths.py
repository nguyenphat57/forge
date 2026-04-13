from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


BUNDLE_ROOT_ENV_VAR = "FORGE_BUNDLE_ROOT"


def resolve_bundle_root() -> Path:
    override = os.environ.get(BUNDLE_ROOT_ENV_VAR)
    if isinstance(override, str) and override.strip():
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


ROOT_DIR = resolve_bundle_root()
PREFERENCES_SCHEMA_PATH = ROOT_DIR / "data" / "preferences-schema.json"
OUTPUT_CONTRACTS_PATH = ROOT_DIR / "data" / "output-contracts.json"
INSTALL_MANIFEST_PATH = ROOT_DIR / "INSTALL-MANIFEST.json"
BUILD_MANIFEST_PATH = ROOT_DIR / "BUILD-MANIFEST.json"
DEFAULT_FALLBACK_STATE_ROOT = Path.home() / ".forge"
GLOBAL_PREFERENCES_RELATIVE_PATH = Path("state") / "preferences.json"
LEGACY_GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH = Path("state") / "extra_preferences.json"
GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH = LEGACY_GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH
LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH = Path(".brain") / "preferences.json"


@lru_cache(maxsize=1)
def load_install_manifest() -> dict | None:
    if not INSTALL_MANIFEST_PATH.exists():
        return None
    manifest = json.loads(INSTALL_MANIFEST_PATH.read_text(encoding="utf-8"))
    return manifest if isinstance(manifest, dict) else None


@lru_cache(maxsize=1)
def load_build_manifest() -> dict | None:
    if not BUILD_MANIFEST_PATH.exists():
        return None
    manifest = json.loads(BUILD_MANIFEST_PATH.read_text(encoding="utf-8"))
    return manifest if isinstance(manifest, dict) else None


@lru_cache(maxsize=1)
def current_bundle_name() -> str:
    manifest = load_build_manifest()
    if manifest is not None:
        package_name = manifest.get("package")
        if isinstance(package_name, str) and package_name.strip():
            return package_name.strip()
    return ROOT_DIR.name


def resolve_installed_state_root() -> Path | None:
    manifest = load_install_manifest()
    if manifest is not None:
        state = manifest.get("state")
        if isinstance(state, dict):
            root = state.get("root")
            if isinstance(root, str) and root.strip():
                return Path(root).expanduser().resolve()

    if ROOT_DIR.parent.name == "skills":
        return (ROOT_DIR.parent.parent / ROOT_DIR.name).resolve()
    return None


def resolve_manifest_state_root() -> Path | None:
    manifest = load_build_manifest()
    if manifest is None:
        return None

    state = manifest.get("state")
    if not isinstance(state, dict):
        return None
    dev_root = state.get("dev_root")
    if not isinstance(dev_root, dict):
        return None

    strategy = dev_root.get("strategy")
    relative = dev_root.get("path_relative")
    if not isinstance(strategy, str) or not isinstance(relative, str) or not relative.strip():
        return None

    if strategy == "bundle-parent-relative":
        return (ROOT_DIR.parent / relative).resolve()

    if strategy == "host-home-relative":
        env_var = dev_root.get("env_var")
        default_home_relative = dev_root.get("default_home_relative")
        candidate = os.environ.get(env_var) if isinstance(env_var, str) and env_var.strip() else None
        if candidate:
            base = Path(candidate).expanduser().resolve()
        elif isinstance(default_home_relative, str) and default_home_relative.strip():
            base = (Path.home() / default_home_relative).resolve()
        else:
            return None
        return (base / relative).resolve()

    return None


def resolve_bundle_default_state_root() -> Path | None:
    manifest_state_root = resolve_manifest_state_root()
    if manifest_state_root is not None:
        return manifest_state_root
    if current_bundle_name() == "forge-core":
        return (ROOT_DIR.parent / "forge-core-state").resolve()
    return None


def resolve_installed_preferences_path() -> Path | None:
    manifest = load_install_manifest()
    if manifest is not None:
        state = manifest.get("state")
        if isinstance(state, dict):
            path = state.get("preferences_path")
            if isinstance(path, str) and path.strip():
                return Path(path).expanduser().resolve()

    state_root = resolve_installed_state_root()
    if state_root is None:
        return None
    return state_root / GLOBAL_PREFERENCES_RELATIVE_PATH


def resolve_installed_extra_preferences_path() -> Path | None:
    installed_preferences_path = resolve_installed_preferences_path()
    if installed_preferences_path is not None:
        return installed_preferences_path.with_name(LEGACY_GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH.name)

    state_root = resolve_installed_state_root()
    if state_root is None:
        return None
    return state_root / LEGACY_GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH


def resolve_forge_home(forge_home: Path | str | None = None) -> Path:
    candidate = forge_home if forge_home is not None else os.environ.get("FORGE_HOME")
    if candidate is not None:
        return Path(candidate).expanduser().resolve()

    installed_state_root = resolve_installed_state_root()
    if installed_state_root is not None:
        return installed_state_root

    bundle_default_state_root = resolve_bundle_default_state_root()
    if bundle_default_state_root is not None:
        return bundle_default_state_root

    return DEFAULT_FALLBACK_STATE_ROOT.resolve()


def resolve_global_preferences_path(forge_home: Path | str | None = None) -> Path:
    if forge_home is None and os.environ.get("FORGE_HOME") is None:
        installed_preferences_path = resolve_installed_preferences_path()
        if installed_preferences_path is not None:
            return installed_preferences_path
    return resolve_forge_home(forge_home) / GLOBAL_PREFERENCES_RELATIVE_PATH


def resolve_global_extra_preferences_path(forge_home: Path | str | None = None) -> Path:
    if forge_home is None and os.environ.get("FORGE_HOME") is None:
        installed_extra_path = resolve_installed_extra_preferences_path()
        if installed_extra_path is not None:
            return installed_extra_path
    return resolve_forge_home(forge_home) / LEGACY_GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH


def resolve_workspace_preferences_path(workspace: Path | None = None) -> Path:
    root = Path(workspace).resolve() if workspace is not None else Path.cwd()
    return root / LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH
