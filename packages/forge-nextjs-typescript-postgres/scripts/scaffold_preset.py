from __future__ import annotations

import argparse
import json
from pathlib import Path

from companion_common import ROOT_DIR, load_capabilities


PLACEHOLDERS = {"__FORGE_PROJECT_NAME__": "Forge App", "__FORGE_PACKAGE_NAME__": "forge-app"}


def _render_text(text: str, project_name: str) -> str:
    replacements = dict(PLACEHOLDERS)
    replacements["__FORGE_PROJECT_NAME__"] = project_name
    replacements["__FORGE_PACKAGE_NAME__"] = project_name.lower().replace(" ", "-")
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def build_report(workspace: Path, preset_id: str, project_name: str, apply: bool) -> dict:
    capabilities = load_capabilities()
    presets = {item["id"]: item for item in capabilities.get("init_presets", []) if isinstance(item, dict) and item.get("id")}
    if preset_id not in presets:
        raise ValueError(f"Unknown preset: {preset_id}")
    template_root = ROOT_DIR / presets[preset_id]["template_dir"]
    created_directories: list[str] = []
    created_files: list[str] = []
    reused_paths: list[str] = []
    if apply:
        workspace.mkdir(parents=True, exist_ok=True)
    for directory in sorted(path for path in template_root.rglob("*") if path.is_dir()):
        target = workspace / directory.relative_to(template_root)
        if target.exists():
            reused_paths.append(str(target))
            continue
        created_directories.append(str(target))
        if apply:
            target.mkdir(parents=True, exist_ok=True)
    for source in sorted(path for path in template_root.rglob("*") if path.is_file()):
        target = workspace / source.relative_to(template_root)
        if target.exists():
            reused_paths.append(str(target))
            continue
        created_files.append(str(target))
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_render_text(source.read_text(encoding="utf-8"), project_name), encoding="utf-8")
    return {
        "status": "PASS",
        "companion": capabilities.get("id"),
        "preset": preset_id,
        "workspace": str(workspace),
        "applied": apply,
        "created_directories": created_directories,
        "created_files": created_files,
        "reused_paths": reused_paths,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a Next.js TypeScript Postgres companion preset.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--preset", default="minimal-saas", help="Preset id")
    parser.add_argument("--project-name", default="Forge App", help="Project name placeholder")
    parser.add_argument("--apply", action="store_true", help="Write files to disk")
    parser.add_argument("--format", choices=["text", "json"], default="json", help="Output format")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve(), args.preset, args.project_name, args.apply)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
