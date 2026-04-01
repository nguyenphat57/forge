from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from bundle_fingerprint import compute_bundle_fingerprint
from host_artifact_manifest import MANIFEST_PATH, generated_host_artifact_records_for_bundle
from host_artifacts_support import ensure_generated_host_artifacts
from overlay_route_fixtures import materialize_overlay_route_fixtures
from package_matrix import PACKAGE_MATRIX_PATH, bundle_package_spec, bundle_required_path_texts, bundle_required_paths
from release_package_specs import discover_package_specs
from release_fs import IGNORE_PATTERNS, copy_file, copy_tree as copy_tree_with_retries, remove_path, remove_tree, should_ignore_relative_path
from release_registry import materialize_overlay_registry


ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = ROOT_DIR / "packages"
DIST_DIR = ROOT_DIR / "dist"
CORE_DIR = PACKAGES_DIR / "forge-core"
VERSION_FILE = ROOT_DIR / "VERSION"
BUNDLE_BUILD_ATTEMPTS = 3
BUNDLE_BUILD_DELAY_SECONDS = 0.2
BUNDLE_READY_ATTEMPTS = 10
BUNDLE_READY_DELAY_SECONDS = 0.1

def read_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError(f"VERSION file is empty: {VERSION_FILE}")
    return version

def resolve_git_revision() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return None
    revision = completed.stdout.strip()
    return revision or None

def clean_dir(path: Path) -> None:
    if path.exists():
        remove_tree(path)

def copy_tree(source: Path, destination: Path) -> None:
    copy_tree_with_retries(source, destination, dirs_exist_ok=True, ignore=IGNORE_PATTERNS)


def prune_cached_python_artifacts(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.name == "__pycache__" or path.suffix.lower() == ".pyc":
            remove_path(path)


def apply_overlay(overlay_dir: Path, destination: Path) -> None:
    if not overlay_dir.exists():
        return
    for path in sorted(overlay_dir.rglob("*")):
        relative = path.relative_to(overlay_dir)
        if should_ignore_relative_path(relative):
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        copy_file(path, target)


def build_state_metadata(package_name: str, host: str, runtime_state: dict | None = None) -> dict | None:
    if isinstance(runtime_state, dict):
        return runtime_state
    if package_name == "forge-core":
        return {
            "scope": "adapter-global",
            "preferences_relative_path": "state/preferences.json",
            "extra_preferences_relative_path": "state/extra_preferences.json",
            "runtime_tools_relative_path": "state/runtime-tools.json",
            "dev_root": {
                "strategy": "bundle-parent-relative",
                "path_relative": "forge-core-state",
            }
        }
    if host == "codex":
        return {
            "scope": "adapter-global",
            "preferences_relative_path": "state/preferences.json",
            "extra_preferences_relative_path": "state/extra_preferences.json",
            "runtime_tools_relative_path": "state/runtime-tools.json",
            "dev_root": {
                "strategy": "host-home-relative",
                "env_var": "CODEX_HOME",
                "default_home_relative": ".codex",
                "path_relative": package_name,
            }
        }
    if host == "antigravity":
        return {
            "scope": "adapter-global",
            "preferences_relative_path": "state/preferences.json",
            "extra_preferences_relative_path": "state/extra_preferences.json",
            "runtime_tools_relative_path": "state/runtime-tools.json",
            "dev_root": {
                "strategy": "host-home-relative",
                "env_var": "GEMINI_HOME",
                "default_home_relative": ".gemini/antigravity",
                "path_relative": package_name,
            }
        }
    return None


def write_build_manifest(
    destination: Path,
    package_name: str,
    host: str,
    source: str,
    metadata: dict[str, str | None],
    *,
    state_metadata: dict | None = None,
) -> None:
    package_spec = bundle_package_spec(package_name)
    manifest = {
        "package": package_name,
        "host": host,
        "source": source,
        "version": metadata["version"],
        "git_revision": metadata["git_revision"],
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packaging": {
            "matrix_path": str(PACKAGE_MATRIX_PATH.relative_to(ROOT_DIR).as_posix()),
            "default_target_strategy": package_spec["default_target_strategy"],
            "required_bundle_paths": bundle_required_path_texts(package_name),
        },
        "bundle_fingerprint": compute_bundle_fingerprint(destination),
        "generated_artifacts": {
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT_DIR).as_posix()),
            "artifacts": generated_host_artifact_records_for_bundle(package_name, output_root=destination),
        },
    }
    state_metadata = state_metadata or build_state_metadata(package_name, host)
    if state_metadata is not None:
        manifest["state"] = state_metadata
    (destination / "BUILD-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def required_bundle_paths(destination: Path, package_name: str, host: str) -> list[Path]:
    del host
    paths = bundle_required_paths(package_name, destination)
    build_manifest_path = destination / "BUILD-MANIFEST.json"
    if build_manifest_path not in paths:
        paths.append(build_manifest_path)
    return paths


def verify_host_artifacts(destination: Path, package_name: str) -> None:
    from install_bundle_host import render_antigravity_global_gemini, render_codex_global_agents

    if package_name == "forge-codex":
        template_path = destination / "AGENTS.global.md"
        render_codex_global_agents(
            template_path.read_text(encoding="utf-8"),
            destination.parent,
            destination,
        )
        return
    if package_name == "forge-antigravity":
        template_path = destination / "GEMINI.global.md"
        render_antigravity_global_gemini(
            template_path.read_text(encoding="utf-8"),
            destination.parent,
            destination,
        )
        return


def wait_for_bundle_ready(destination: Path, package_name: str, host: str) -> None:
    for attempt in range(BUNDLE_READY_ATTEMPTS):
        missing = [path for path in required_bundle_paths(destination, package_name, host) if not path.exists()]
        if not missing:
            return
        if attempt < BUNDLE_READY_ATTEMPTS - 1:
            time.sleep(BUNDLE_READY_DELAY_SECONDS * (attempt + 1))
            continue
        raise FileNotFoundError(f"Missing build artifacts for {package_name}: {missing[0]}")


def build_core_bundle(metadata: dict[str, str | None]) -> dict:
    destination = DIST_DIR / "forge-core"
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(CORE_DIR, destination)
        write_build_manifest(destination, "forge-core", "generic", "packages/forge-core", metadata)
        prune_cached_python_artifacts(destination)
        try:
            wait_for_bundle_ready(destination, "forge-core", "generic")
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {"name": "forge-core", "path": str(destination), "host": "generic", "version": metadata["version"]}


def build_adapter_bundle(spec: dict, metadata: dict[str, str | None]) -> dict:
    package_dir = spec["package_dir"]
    destination = DIST_DIR / spec["name"]
    overlay_dir = package_dir / spec["overlay_dir"]
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(CORE_DIR, destination)
        apply_overlay(overlay_dir, destination)
        materialize_overlay_registry(CORE_DIR, overlay_dir, destination)
        materialize_overlay_route_fixtures(spec["name"], destination)
        write_build_manifest(
            destination,
            spec["name"],
            spec["host"],
            str(package_dir.relative_to(ROOT_DIR)),
            metadata,
            state_metadata=build_state_metadata(spec["name"], spec["host"], spec.get("state")),
        )
        prune_cached_python_artifacts(destination)
        try:
            wait_for_bundle_ready(destination, spec["name"], spec["host"])
            verify_host_artifacts(destination, spec["name"])
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {
        "name": spec["name"],
        "path": str(destination),
        "host": spec["host"],
        "version": metadata["version"],
    }


def build_runtime_bundle(spec: dict, metadata: dict[str, str | None]) -> dict:
    package_dir = spec["package_dir"]
    destination = DIST_DIR / spec["name"]
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(package_dir, destination)
        write_build_manifest(
            destination,
            spec["name"],
            spec["host"],
            str(package_dir.relative_to(ROOT_DIR)),
            metadata,
            state_metadata=build_state_metadata(spec["name"], spec["host"], spec.get("state")),
        )
        prune_cached_python_artifacts(destination)
        try:
            wait_for_bundle_ready(destination, spec["name"], spec["host"])
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {"name": spec["name"], "path": str(destination), "host": spec["host"], "version": metadata["version"]}


def build_companion_bundle(spec: dict, metadata: dict[str, str | None]) -> dict:
    return build_runtime_bundle(spec, metadata)


def build_all() -> list[dict]:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    host_artifact_report = ensure_generated_host_artifacts(check=True)
    if host_artifact_report["status"] != "PASS":
        first_stale = host_artifact_report["stale_outputs"][0]["path"]
        raise ValueError(
            "Generated host artifacts are stale. "
            f"Run `python scripts/generate_host_artifacts.py --apply`. First stale output: {first_stale}"
        )
    metadata = {"version": read_version(), "git_revision": resolve_git_revision()}
    all_specs = discover_package_specs(PACKAGES_DIR, include_examples=True)
    release_specs = [spec for spec in all_specs if spec.get("distribution") != "example"]
    release_bundle_names = {"forge-core", *(spec["name"] for spec in release_specs)}
    for spec in all_specs:
        if spec["name"] not in release_bundle_names:
            clean_dir(DIST_DIR / spec["name"])
    outputs = [build_core_bundle(metadata)]
    for spec in release_specs:
        if spec["kind"] == "adapter":
            outputs.append(build_adapter_bundle(spec, metadata))
            continue
        if spec["kind"] == "companion":
            outputs.append(build_companion_bundle(spec, metadata))
            continue
        outputs.append(build_runtime_bundle(spec, metadata))
    prune_cached_python_artifacts(DIST_DIR)
    for item in outputs:
        wait_for_bundle_ready(Path(item["path"]), item["name"], item["host"])
    return outputs


def format_text(outputs: list[dict]) -> str:
    version = outputs[0]["version"] if outputs else read_version()
    lines = [f"Forge Release Build (version {version})"]
    for item in outputs:
        lines.append(f"- {item['name']} [{item['host']}] -> {item['path']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Forge release bundles from core, adapters, and runtime tools.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    outputs = build_all()
    if args.format == "json":
        print(json.dumps({"bundles": outputs}, indent=2, ensure_ascii=False))
    else:
        print(format_text(outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
