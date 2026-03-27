from __future__ import annotations

from preferences_contract import (
    PREFERENCE_ALIASES,
    load_output_contract_profiles,
    load_preferences_schema,
    normalize_preferences,
    preference_defaults,
    resolve_output_contract,
)
from preferences_paths import (
    BUILD_MANIFEST_PATH,
    DEFAULT_FALLBACK_STATE_ROOT,
    GLOBAL_EXTRA_PREFERENCES_RELATIVE_PATH,
    GLOBAL_PREFERENCES_RELATIVE_PATH,
    INSTALL_MANIFEST_PATH,
    LEGACY_WORKSPACE_PREFERENCES_RELATIVE_PATH,
    OUTPUT_CONTRACTS_PATH,
    PREFERENCES_SCHEMA_PATH,
    ROOT_DIR,
    load_build_manifest,
    load_install_manifest,
    resolve_forge_home,
    resolve_global_extra_preferences_path,
    resolve_global_preferences_path,
    resolve_installed_extra_preferences_path,
    resolve_installed_preferences_path,
    resolve_installed_state_root,
    resolve_workspace_preferences_path,
)
from preferences_store import load_preferences, write_preferences
