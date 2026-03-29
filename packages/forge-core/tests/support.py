from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
WORKSPACES_DIR = FIXTURES_DIR / "workspaces"
FORGE_HOMES_DIR = FIXTURES_DIR / "forge-homes"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import common  # noqa: E402


def build_route_args(
    prompt: str,
    *,
    repo_signals: list[str] | None = None,
    workspace_router: Path | None = None,
    changed_files: int | None = None,
    has_harness: str = "auto",
) -> Namespace:
    return Namespace(
        prompt=prompt,
        repo_signal=repo_signals or [],
        workspace_router=workspace_router,
        changed_files=changed_files,
        has_harness=has_harness,
        format="json",
        persist=False,
        output_dir=None,
    )


def load_json_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def workspace_fixture(name: str) -> Path:
    return WORKSPACES_DIR / name


def resolve_reference_companion_package() -> Path:
    candidates = [ROOT_DIR.parent / "forge-nextjs-typescript-postgres"]
    if len(ROOT_DIR.parents) >= 2:
        candidates.append(ROOT_DIR.parents[1] / "packages" / "forge-nextjs-typescript-postgres")
    for candidate in candidates:
        if (candidate / "companion.json").exists():
            return candidate.resolve()
    return candidates[0].resolve()


@contextmanager
def temporary_workspace(name: str = "workspace"):
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / name
        workspace.mkdir(parents=True, exist_ok=True)
        yield workspace


@contextmanager
def copied_workspace_fixture(name: str, *, target_name: str = "workspace"):
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / target_name
        shutil.copytree(workspace_fixture(name), workspace)
        yield workspace


def forge_home_fixture(name: str) -> Path:
    return FORGE_HOMES_DIR / name


def bundle_package_name() -> str:
    manifest_path = ROOT_DIR / "BUILD-MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package_name = manifest.get("package")
        if isinstance(package_name, str) and package_name.strip():
            return package_name.strip()
    return ROOT_DIR.name


def is_core_bundle() -> bool:
    return bundle_package_name() == "forge-core"


def load_output_contract_profiles() -> dict | None:
    if not common.OUTPUT_CONTRACTS_PATH.exists():
        return None
    payload = json.loads(common.OUTPUT_CONTRACTS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def expected_output_contract(extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return {}

    contract: dict[str, object] = {}
    profiles = load_output_contract_profiles()
    language_profile: dict[str, object] | None = None

    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = common.normalize_choice_token(language)
        contract["language"] = normalized_language
        if isinstance(profiles, dict):
            languages = profiles.get("languages")
            if isinstance(languages, dict):
                profile = languages.get(normalized_language)
                if isinstance(profile, dict):
                    language_profile = profile
                    profile_contract = profile.get("contract")
                    if isinstance(profile_contract, dict):
                        contract.update(copy.deepcopy(profile_contract))

    orthography = extra.get("orthography")
    if isinstance(orthography, str) and orthography.strip():
        normalized_orthography = common.normalize_choice_token(orthography)
        contract["orthography"] = normalized_orthography
        if isinstance(profiles, dict):
            orthographies = profiles.get("orthographies")
            if isinstance(orthographies, dict):
                profile = orthographies.get(normalized_orthography)
                if isinstance(profile, dict):
                    contract.update(copy.deepcopy(profile))

    tone_detail = extra.get("tone_detail")
    if isinstance(tone_detail, str) and tone_detail.strip():
        contract["tone_detail"] = tone_detail.strip()

    custom_rules = extra.get("custom_rules")
    if isinstance(custom_rules, list):
        normalized_rules = [item.strip() for item in custom_rules if isinstance(item, str) and item.strip()]
        if normalized_rules:
            contract["custom_rules"] = normalized_rules

    if "orthography" not in contract and isinstance(language_profile, dict):
        default_orthography = language_profile.get("default_orthography")
        if isinstance(default_orthography, str) and default_orthography.strip():
            normalized_orthography = common.normalize_choice_token(default_orthography)
            contract["orthography"] = normalized_orthography
            if isinstance(profiles, dict):
                orthographies = profiles.get("orthographies")
                if isinstance(orthographies, dict):
                    profile = orthographies.get(normalized_orthography)
                    if isinstance(profile, dict):
                        contract.update(copy.deepcopy(profile))

    return contract


def run_python_script(
    script_name: str,
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPTS_DIR / script_name), *args]
    merged_env = os.environ.copy()
    merged_env.setdefault("FORGE_HOME", str(forge_home_fixture("empty")))
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=str(cwd or ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=merged_env,
    )
