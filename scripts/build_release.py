from __future__ import annotations

import argparse
import copy
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from bundle_fingerprint import bundle_fingerprint_matches_manifest, compute_bundle_fingerprint, compute_path_fingerprint, fingerprint_matches
from host_artifact_manifest import MANIFEST_PATH, generated_host_artifact_records_for_bundle
from host_artifacts_support import ensure_generated_host_artifacts
from package_matrix import (
    PACKAGE_MATRIX_PATH,
    bundle_names,
    bundle_package_spec,
    bundle_required_path_texts,
    bundle_required_paths,
    sibling_skill_names,
    sibling_skill_source_dir,
)
from release_package_specs import discover_package_specs
from release_fs import IGNORE_PATTERNS, copy_file, copy_tree as copy_tree_with_retries, remove_path, remove_tree, should_ignore_relative_path
from release_registry import materialize_overlay_registry
from skill_bundle_composer import ensure_generated_overlay_skills, write_composed_adapter_skill


ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = ROOT_DIR / "packages"
DIST_DIR = ROOT_DIR / "dist"
CORE_DIR = PACKAGES_DIR / "forge-core"
VERSION_FILE = ROOT_DIR / "VERSION"
BUNDLE_BUILD_ATTEMPTS = 3
BUNDLE_BUILD_DELAY_SECONDS = 0.2
BUNDLE_READY_ATTEMPTS = 10
BUNDLE_READY_DELAY_SECONDS = 0.1
FORBIDDEN_RUNTIME_DIRS = ("scripts", "engine")
COMMON_BUILD_INPUTS = (
    ROOT_DIR / "VERSION",
    ROOT_DIR / "docs" / "release" / "package-matrix.json",
    ROOT_DIR / "docs" / "architecture" / "host-artifacts-manifest.json",
    ROOT_DIR / "docs" / "current" / "target-state.md",
    ROOT_DIR / "scripts" / "build_release.py",
    ROOT_DIR / "scripts" / "bundle_fingerprint.py",
    ROOT_DIR / "scripts" / "host_artifact_manifest.py",
    ROOT_DIR / "scripts" / "host_artifacts_support.py",
    ROOT_DIR / "scripts" / "operator_surface_support.py",
    ROOT_DIR / "scripts" / "package_matrix.py",
    ROOT_DIR / "scripts" / "generate_overlay_skills.py",
    ROOT_DIR / "scripts" / "release_package_specs.py",
    ROOT_DIR / "scripts" / "release_registry.py",
    ROOT_DIR / "scripts" / "skill_bundle_composer.py",
)

def read_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError(f"VERSION file is empty: {VERSION_FILE}")
    return version

def resolve_git_revision(root: Path = ROOT_DIR) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return None
    revision = completed.stdout.strip()
    return revision or None


def resolve_git_tree_provenance(root: Path = ROOT_DIR) -> dict[str, object]:
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all", "--", "."],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return {
            "available": False,
            "state": "unknown",
            "modified_files": [],
            "untracked_files": [],
        }

    modified_files: list[str] = []
    untracked_files: list[str] = []
    for line in completed.stdout.splitlines():
        if len(line) < 3:
            continue
        status = line[:2]
        relative = line[3:]
        if " -> " in relative:
            relative = relative.split(" -> ", 1)[-1]
        if status == "??":
            untracked_files.append(relative)
        else:
            modified_files.append(relative)

    if modified_files and untracked_files:
        state = "mixed"
    elif modified_files:
        state = "modified"
    elif untracked_files:
        state = "untracked"
    else:
        state = "clean"

    return {
        "available": True,
        "state": state,
        "modified_files": modified_files,
        "untracked_files": untracked_files,
    }

def clean_dir(path: Path) -> None:
    if path.exists():
        remove_tree(path)

def copy_tree(source: Path, destination: Path) -> None:
    copy_tree_with_retries(source, destination, dirs_exist_ok=True, ignore=IGNORE_PATTERNS)


def prune_cached_python_artifacts(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.name == "__pycache__" or path.suffix.lower() == ".pyc":
            remove_path(path)


def remove_bundled_skill_tree(destination: Path) -> None:
    skill_dir = destination / "skills"
    if skill_dir.exists():
        remove_tree(skill_dir)


def remove_forbidden_runtime_dirs(destination: Path) -> None:
    for dirname in FORBIDDEN_RUNTIME_DIRS:
        path = destination / dirname
        if path.exists():
            remove_tree(path)


def has_forbidden_runtime_dirs(destination: Path) -> bool:
    return any((destination / dirname).exists() for dirname in FORBIDDEN_RUNTIME_DIRS)


def copy_runtime_docs(destination: Path) -> None:
    copy_file(ROOT_DIR / "docs" / "current" / "target-state.md", destination / "docs" / "current" / "target-state.md")


def apply_overlay(overlay_dir: Path, destination: Path, *, ignored_relative_paths: set[str] | None = None) -> None:
    ignored_relative_paths = ignored_relative_paths or set()
    if not overlay_dir.exists():
        return
    for path in sorted(overlay_dir.rglob("*")):
        relative = path.relative_to(overlay_dir)
        if should_ignore_relative_path(relative):
            continue
        if relative.as_posix() in ignored_relative_paths:
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
            "dev_root": {
                "strategy": "bundle-parent-relative",
                "path_relative": "forge-core-state",
            }
        }
    if host == "codex":
        return {
            "scope": "adapter-global",
            "preferences_relative_path": "state/preferences.json",
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
            "dev_root": {
                "strategy": "host-home-relative",
                "env_var": "GEMINI_HOME",
                "default_home_relative": ".gemini/antigravity",
                "path_relative": package_name,
            }
        }
    return None


def build_input_paths(package_name: str, *, package_dir: Path | None = None, overlay_dir: Path | None = None) -> list[Path]:
    paths = list(COMMON_BUILD_INPUTS)
    if package_name in sibling_skill_names():
        paths.append(sibling_skill_source_dir(package_name))
        return paths
    if package_name == "forge-core":
        paths.append(CORE_DIR)
        return paths
    if package_dir is None:
        raise ValueError(f"package_dir is required for bundle inputs: {package_name}")
    if overlay_dir is not None:
        paths.extend([CORE_DIR, overlay_dir])
        return paths
    paths.append(package_dir)
    return paths


def compute_source_input_fingerprint(package_name: str, *, package_dir: Path | None = None, overlay_dir: Path | None = None) -> dict[str, object]:
    return compute_path_fingerprint(
        build_input_paths(package_name, package_dir=package_dir, overlay_dir=overlay_dir),
        relative_to=ROOT_DIR,
    )


def write_build_manifest(
    destination: Path,
    package_name: str,
    host: str,
    source: str,
    metadata: dict[str, object],
    *,
    state_metadata: dict | None = None,
    source_input_fingerprint: dict | None = None,
) -> None:
    package_spec = bundle_package_spec(package_name)
    git_tree = metadata.get("git_tree")
    if not isinstance(git_tree, dict):
        git_tree = resolve_git_tree_provenance()
    manifest = {
        "package": package_name,
        "host": host,
        "source": source,
        "version": metadata["version"],
        "git_revision": metadata["git_revision"],
        "git_tree": git_tree,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packaging": {
            "matrix_path": str(PACKAGE_MATRIX_PATH.relative_to(ROOT_DIR).as_posix()),
            "default_target_strategy": package_spec["default_target_strategy"],
            "required_bundle_paths": bundle_required_path_texts(package_name),
        },
        "bundle_fingerprint": compute_bundle_fingerprint(destination),
        "source_input_fingerprint": copy.deepcopy(source_input_fingerprint),
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


def write_sibling_skill_manifest(
    destination: Path,
    package_name: str,
    metadata: dict[str, object],
    *,
    source_input_fingerprint: dict | None = None,
) -> None:
    source_dir = sibling_skill_source_dir(package_name)
    required_bundle_paths = ["BUILD-MANIFEST.json"] + [
        str(path.relative_to(source_dir).as_posix())
        for path in sorted(source_dir.rglob("*"))
        if path.is_file() and not should_ignore_relative_path(path.relative_to(source_dir))
    ]
    manifest = {
        "package": package_name,
        "host": "skill",
        "source": str(source_dir.relative_to(ROOT_DIR)),
        "version": metadata["version"],
        "git_revision": metadata["git_revision"],
        "git_tree": metadata["git_tree"],
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packaging": {
            "matrix_path": str(PACKAGE_MATRIX_PATH.relative_to(ROOT_DIR).as_posix()),
            "default_target_strategy": "sibling-skill",
            "required_bundle_paths": required_bundle_paths,
        },
        "bundle_fingerprint": compute_bundle_fingerprint(destination),
        "source_input_fingerprint": copy.deepcopy(source_input_fingerprint),
        "generated_artifacts": {
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT_DIR).as_posix()),
            "artifacts": [],
        },
    }
    (destination / "BUILD-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def required_bundle_paths(destination: Path, package_name: str, host: str) -> list[Path]:
    del host
    if package_name in sibling_skill_names():
        source_dir = sibling_skill_source_dir(package_name)
        relative_files = [
            path.relative_to(source_dir)
            for path in sorted(source_dir.rglob("*"))
            if path.is_file() and not should_ignore_relative_path(path.relative_to(source_dir))
        ]
        return [destination / "BUILD-MANIFEST.json", *[destination / path for path in relative_files]]
    paths = bundle_required_paths(package_name, destination)
    build_manifest_path = destination / "BUILD-MANIFEST.json"
    if build_manifest_path not in paths:
        paths.append(build_manifest_path)
    return paths


def load_existing_build_manifest(destination: Path) -> dict[str, object] | None:
    manifest_path = destination / "BUILD-MANIFEST.json"
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def can_skip_build(
    destination: Path,
    package_name: str,
    host: str,
    metadata: dict[str, object],
    *,
    source_input_fingerprint: dict[str, object],
) -> bool:
    manifest = load_existing_build_manifest(destination)
    if manifest is None:
        return False
    if manifest.get("version") != metadata["version"]:
        return False
    if manifest.get("git_revision") != metadata["git_revision"]:
        return False
    if manifest.get("git_tree") != metadata["git_tree"]:
        return False
    if not fingerprint_matches(manifest.get("source_input_fingerprint"), source_input_fingerprint):
        return False
    if has_forbidden_runtime_dirs(destination):
        return False
    missing = [path for path in required_bundle_paths(destination, package_name, host) if not path.exists()]
    if missing:
        return False
    matches_manifest, _, _ = bundle_fingerprint_matches_manifest(destination, manifest)
    return matches_manifest


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


def build_core_bundle(metadata: dict[str, object], *, force: bool = False) -> dict:
    destination = DIST_DIR / "forge-core"
    source_input_fingerprint = compute_source_input_fingerprint("forge-core")
    if not force and can_skip_build(
        destination,
        "forge-core",
        "generic",
        metadata,
        source_input_fingerprint=source_input_fingerprint,
    ):
        return {
            "name": "forge-core",
            "path": str(destination),
            "host": "generic",
            "version": metadata["version"],
            "skipped": True,
        }
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(CORE_DIR, destination)
        remove_bundled_skill_tree(destination)
        remove_forbidden_runtime_dirs(destination)
        copy_runtime_docs(destination)
        write_build_manifest(
            destination,
            "forge-core",
            "generic",
            "packages/forge-core",
            metadata,
            source_input_fingerprint=source_input_fingerprint,
        )
        prune_cached_python_artifacts(destination)
        try:
            wait_for_bundle_ready(destination, "forge-core", "generic")
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {"name": "forge-core", "path": str(destination), "host": "generic", "version": metadata["version"], "skipped": False}


def build_adapter_bundle(spec: dict, metadata: dict[str, object], *, force: bool = False) -> dict:
    package_dir = spec["package_dir"]
    destination = DIST_DIR / spec["name"]
    overlay_dir = package_dir / spec["overlay_dir"]
    source_input_fingerprint = compute_source_input_fingerprint(spec["name"], package_dir=package_dir, overlay_dir=overlay_dir)
    if not force and can_skip_build(
        destination,
        spec["name"],
        spec["host"],
        metadata,
        source_input_fingerprint=source_input_fingerprint,
    ):
        return {
            "name": spec["name"],
            "path": str(destination),
            "host": spec["host"],
            "version": metadata["version"],
            "skipped": True,
        }
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(CORE_DIR, destination)
        remove_bundled_skill_tree(destination)
        remove_forbidden_runtime_dirs(destination)
        copy_runtime_docs(destination)
        apply_overlay(
            overlay_dir,
            destination,
            ignored_relative_paths={"SKILL.md", "SKILL.delta.md"},
        )
        materialize_overlay_registry(CORE_DIR, overlay_dir, destination)
        write_composed_adapter_skill(spec["name"], destination / "SKILL.md")
        write_build_manifest(
            destination,
            spec["name"],
            spec["host"],
            str(package_dir.relative_to(ROOT_DIR)),
            metadata,
            state_metadata=build_state_metadata(spec["name"], spec["host"], spec.get("state")),
            source_input_fingerprint=source_input_fingerprint,
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
        "skipped": False,
    }


def build_sibling_skill_bundle(package_name: str, metadata: dict[str, object], *, force: bool = False) -> dict:
    destination = DIST_DIR / package_name
    source_dir = sibling_skill_source_dir(package_name)
    source_input_fingerprint = compute_source_input_fingerprint(package_name)
    if not force and can_skip_build(
        destination,
        package_name,
        "skill",
        metadata,
        source_input_fingerprint=source_input_fingerprint,
    ):
        return {
            "name": package_name,
            "path": str(destination),
            "host": "skill",
            "version": metadata["version"],
            "skipped": True,
        }
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(source_dir, destination)
        write_sibling_skill_manifest(
            destination,
            package_name,
            metadata,
            source_input_fingerprint=source_input_fingerprint,
        )
        prune_cached_python_artifacts(destination)
        try:
            wait_for_bundle_ready(destination, package_name, "skill")
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {"name": package_name, "path": str(destination), "host": "skill", "version": metadata["version"], "skipped": False}


def build_all(*, force: bool = False) -> list[dict]:
    git_tree = resolve_git_tree_provenance(ROOT_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    host_artifact_report = ensure_generated_host_artifacts(check=True)
    if host_artifact_report["status"] != "PASS":
        first_stale = host_artifact_report["stale_outputs"][0]["path"]
        raise ValueError(
            "Generated host artifacts are stale. "
            f"Run `python scripts/generate_host_artifacts.py --apply`. First stale output: {first_stale}"
        )
    overlay_skill_report = ensure_generated_overlay_skills(check=True)
    if overlay_skill_report["status"] != "PASS":
        first_stale = overlay_skill_report["stale_outputs"][0]["path"]
        raise ValueError(
            "Generated overlay skills are stale. "
            f"Run `python scripts/generate_overlay_skills.py --apply`. First stale output: {first_stale}"
        )
    metadata = {"version": read_version(), "git_revision": resolve_git_revision(), "git_tree": git_tree}
    all_specs = discover_package_specs(PACKAGES_DIR, include_examples=True)
    release_bundle_names = set(bundle_names())
    release_output_names = release_bundle_names | set(sibling_skill_names())
    release_specs = [spec for spec in all_specs if spec["name"] in release_bundle_names]
    for spec in all_specs:
        if spec["name"] not in release_bundle_names:
            clean_dir(DIST_DIR / spec["name"])
    outputs = [build_core_bundle(metadata, force=force)]
    for spec in release_specs:
        if spec["kind"] == "adapter":
            outputs.append(build_adapter_bundle(spec, metadata, force=force))
    for package_name in sibling_skill_names():
        outputs.append(build_sibling_skill_bundle(package_name, metadata, force=force))
    prune_cached_python_artifacts(DIST_DIR)
    for child in DIST_DIR.iterdir():
        if child.is_dir() and child.name not in release_output_names:
            clean_dir(child)
    for item in outputs:
        wait_for_bundle_ready(Path(item["path"]), item["name"], item["host"])
    return outputs


def format_text(outputs: list[dict]) -> str:
    version = outputs[0]["version"] if outputs else read_version()
    lines = [f"Forge Release Build (version {version})"]
    for item in outputs:
        suffix = " (unchanged)" if item.get("skipped") else ""
        lines.append(f"- {item['name']} [{item['host']}] -> {item['path']}{suffix}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Forge release bundles from the core kernel and host adapters.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--force", action="store_true", help="Rebuild every bundle even when dist already matches the current source inputs.")
    args = parser.parse_args()

    outputs = build_all(force=args.force)
    if args.format == "json":
        print(json.dumps({"bundles": outputs}, indent=2, ensure_ascii=False))
    else:
        print(format_text(outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
