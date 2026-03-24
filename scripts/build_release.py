from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = ROOT_DIR / "packages"
DIST_DIR = ROOT_DIR / "dist"
CORE_DIR = PACKAGES_DIR / "forge-core"
VERSION_FILE = ROOT_DIR / "VERSION"
IGNORE_PATTERNS = shutil.ignore_patterns(".forge-artifacts", "__pycache__", "*.pyc", ".pytest_cache")


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
        shutil.rmtree(path)


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=IGNORE_PATTERNS)


def apply_overlay(overlay_dir: Path, destination: Path) -> None:
    if not overlay_dir.exists():
        return
    for path in sorted(overlay_dir.rglob("*")):
        relative = path.relative_to(overlay_dir)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def write_build_manifest(destination: Path, package_name: str, host: str, source: str, metadata: dict[str, str | None]) -> None:
    manifest = {
        "package": package_name,
        "host": host,
        "source": source,
        "version": metadata["version"],
        "git_revision": metadata["git_revision"],
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (destination / "BUILD-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_core_bundle(metadata: dict[str, str | None]) -> dict:
    destination = DIST_DIR / "forge-core"
    clean_dir(destination)
    copy_tree(CORE_DIR, destination)
    write_build_manifest(destination, "forge-core", "generic", "packages/forge-core", metadata)
    return {"name": "forge-core", "path": str(destination), "host": "generic", "version": metadata["version"]}


def build_adapter_bundle(package_dir: Path, metadata: dict[str, str | None]) -> dict:
    manifest = load_adapter_manifest(package_dir)
    destination = DIST_DIR / manifest["name"]
    clean_dir(destination)
    copy_tree(CORE_DIR, destination)
    apply_overlay(package_dir / manifest["overlay_dir"], destination)
    write_build_manifest(
        destination,
        manifest["name"],
        manifest["host"],
        str(package_dir.relative_to(ROOT_DIR)),
        metadata,
    )
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
