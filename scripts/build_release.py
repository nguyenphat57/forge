from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from release_fs import IGNORE_PATTERNS, copy_file, copy_tree as copy_tree_with_retries, remove_tree, should_ignore_relative_path
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


def load_adapter_manifest(package_dir: Path) -> dict:
    return json.loads((package_dir / "adapter.json").read_text(encoding="utf-8"))


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


def build_state_metadata(package_name: str, host: str) -> dict | None:
    if package_name == "forge-core":
        return {
            "dev_root": {
                "strategy": "bundle-parent-relative",
                "path_relative": "forge-core-state",
            }
        }
    if host == "codex":
        return {
            "dev_root": {
                "strategy": "host-home-relative",
                "env_var": "CODEX_HOME",
                "default_home_relative": ".codex",
                "path_relative": package_name,
            }
        }
    if host == "antigravity":
        return {
            "dev_root": {
                "strategy": "host-home-relative",
                "env_var": "GEMINI_HOME",
                "default_home_relative": ".gemini/antigravity",
                "path_relative": package_name,
            }
        }
    return None


def write_build_manifest(destination: Path, package_name: str, host: str, source: str, metadata: dict[str, str | None]) -> None:
    manifest = {
        "package": package_name,
        "host": host,
        "source": source,
        "version": metadata["version"],
        "git_revision": metadata["git_revision"],
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    state_metadata = build_state_metadata(package_name, host)
    if state_metadata is not None:
        manifest["state"] = state_metadata
    (destination / "BUILD-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def required_bundle_paths(destination: Path, package_name: str, host: str) -> list[Path]:
    paths = [
        destination / "BUILD-MANIFEST.json",
        destination / "scripts" / "common.py",
        destination / "scripts" / "preferences.py",
        destination / "scripts" / "help_next_support.py",
        destination / "scripts" / "run_guidance_support.py",
        destination / "scripts" / "verify_bundle.py",
        destination / "scripts" / "resolve_help_next.py",
        destination / "scripts" / "run_with_guidance.py",
    ]
    if package_name == "forge-antigravity":
        paths.extend([
            destination / "GEMINI.global.md",
            destination / "workflows" / "operator" / "bump.md",
        ])
    if package_name == "forge-codex":
        paths.extend([
            destination / "AGENTS.global.md",
            destination / "data" / "orchestrator-registry.json",
        ])
    return paths


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
        try:
            wait_for_bundle_ready(destination, "forge-core", "generic")
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {"name": "forge-core", "path": str(destination), "host": "generic", "version": metadata["version"]}


def build_adapter_bundle(package_dir: Path, metadata: dict[str, str | None]) -> dict:
    manifest = load_adapter_manifest(package_dir)
    destination = DIST_DIR / manifest["name"]
    overlay_dir = package_dir / manifest["overlay_dir"]
    for attempt in range(BUNDLE_BUILD_ATTEMPTS):
        clean_dir(destination)
        copy_tree(CORE_DIR, destination)
        apply_overlay(overlay_dir, destination)
        materialize_overlay_registry(CORE_DIR, overlay_dir, destination)
        write_build_manifest(
            destination,
            manifest["name"],
            manifest["host"],
            str(package_dir.relative_to(ROOT_DIR)),
            metadata,
        )
        try:
            wait_for_bundle_ready(destination, manifest["name"], manifest["host"])
            break
        except FileNotFoundError:
            if attempt == BUNDLE_BUILD_ATTEMPTS - 1:
                raise
            time.sleep(BUNDLE_BUILD_DELAY_SECONDS * (attempt + 1))
    return {
        "name": manifest["name"],
        "path": str(destination),
        "host": manifest["host"],
        "version": metadata["version"],
    }


def build_all() -> list[dict]:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {"version": read_version(), "git_revision": resolve_git_revision()}
    outputs = [build_core_bundle(metadata)]
    for package_dir in sorted(PACKAGES_DIR.iterdir()):
        if not package_dir.is_dir() or package_dir.name == "forge-core":
            continue
        if not (package_dir / "adapter.json").exists():
            continue
        outputs.append(build_adapter_bundle(package_dir, metadata))
    return outputs


def format_text(outputs: list[dict]) -> str:
    version = outputs[0]["version"] if outputs else read_version()
    lines = [f"Forge Release Build (version {version})"]
    for item in outputs:
        lines.append(f"- {item['name']} [{item['host']}] -> {item['path']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Forge release bundles from core + adapter overlays.")
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
