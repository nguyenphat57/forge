from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, preference_defaults, resolve_forge_home, resolve_global_preferences_path
from companion_invoke import invoke_companion_preset
from companion_matching import resolve_companion_preset


IGNORED_EXISTING_ENTRIES = {
    ".git",
    ".gitattributes",
    ".gitignore",
    ".gitkeep",
    ".DS_Store",
    ".forge-artifacts",
}


def detect_workspace_mode(workspace: Path) -> str:
    if not workspace.exists():
        return "greenfield"

    interesting_entries = []
    for entry in workspace.iterdir():
        if entry.name in IGNORED_EXISTING_ENTRIES:
            continue
        if entry.name.startswith(".") and entry.name not in {".brain"}:
            continue
        interesting_entries.append(entry.name)

    return "existing" if interesting_entries else "greenfield"


def build_session_payload(project_name: str | None) -> dict:
    feature = project_name.strip() if project_name else ""
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "working_on": {"feature": feature, "task": "", "status": "idle", "files": []},
        "pending_tasks": [],
        "recent_changes": [],
        "verification": [],
        "decisions_made": [],
    }


def build_plan(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    mode = args.mode if args.mode != "auto" else detect_workspace_mode(workspace)

    directories = [
        workspace / ".brain",
        workspace / "docs",
        workspace / "docs" / "plans",
        workspace / "docs" / "specs",
    ]
    files: list[tuple[Path, str]] = [
        (
            workspace / ".brain" / "session.json",
            json.dumps(build_session_payload(args.project_name), indent=2, ensure_ascii=False) + "\n",
        )
    ]
    if args.seed_continuity:
        files.extend(
            [
                (workspace / ".brain" / "decisions.json", "[]\n"),
                (workspace / ".brain" / "learnings.json", "[]\n"),
            ]
        )
    if args.seed_preferences:
        files.append(
            (
                resolve_global_preferences_path(args.forge_home),
                json.dumps(preference_defaults(), indent=2, ensure_ascii=False) + "\n",
            )
        )

    created_directories: list[str] = []
    created_files: list[str] = []
    reused_paths: list[str] = []
    warnings: list[str] = []

    if args.apply:
        workspace.mkdir(parents=True, exist_ok=True)

    for directory in directories:
        if directory.exists():
            reused_paths.append(str(directory))
            continue
        created_directories.append(str(directory))
        if args.apply:
            directory.mkdir(parents=True, exist_ok=True)

    for path, content in files:
        if path.exists():
            reused_paths.append(str(path))
            continue
        created_files.append(str(path))
        if args.apply:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    preset_report: dict | None = None
    if args.preset:
        preset = resolve_companion_preset(args.preset)
        preset_report = invoke_companion_preset(preset, workspace, args.project_name, args.apply)
        created_directories.extend(item for item in preset_report.get("created_directories", []) if item not in created_directories)
        created_files.extend(item for item in preset_report.get("created_files", []) if item not in created_files)
        reused_paths.extend(item for item in preset_report.get("reused_paths", []) if item not in reused_paths)
        warnings.append(f"Preset scaffold attached via companion `{preset['companion_id']}`.")

    recommended_next_workflow = "brainstorm" if mode == "greenfield" else "plan"
    recommended_action = (
        "Start with `brainstorm` to lock the product direction before implementation."
        if mode == "greenfield"
        else "Start with `plan` against the current repo state before editing."
    )
    if args.seed_continuity:
        recommended_action += " After direction lock, capture any repo-local rules with `capture_continuity.py --constitution`."
    if preset_report is not None:
        recommended_next_workflow = "plan"
        recommended_action = "Run `doctor`, then use `plan` against the scaffolded preset before extending scope."

    return {
        "status": "PASS",
        "workspace": str(workspace),
        "workspace_mode": mode,
        "state_root": str(resolve_forge_home(args.forge_home)),
        "forge_home": str(resolve_forge_home(args.forge_home)),
        "applied": args.apply,
        "seed_preferences": args.seed_preferences,
        "seed_continuity": args.seed_continuity,
        "created_directories": created_directories,
        "created_files": created_files,
        "reused_paths": reused_paths,
        "preset": args.preset,
        "preset_report": preset_report,
        "recommended_next_workflow": recommended_next_workflow,
        "recommended_action": recommended_action,
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Workspace Init",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Mode: {report['workspace_mode']}",
        f"- State root: {report['state_root']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        f"- Seed preferences: {'yes' if report['seed_preferences'] else 'no'}",
        "- Created directories:",
    ]
    if report["created_directories"]:
        for item in report["created_directories"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append("- Created files:")
    if report["created_files"]:
        for item in report["created_files"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append("- Reused paths:")
    if report["reused_paths"]:
        for item in report["reused_paths"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - (none)")

    lines.append(f"- Next workflow: {report['recommended_next_workflow']}")
    lines.append(f"- Recommended action: {report['recommended_action']}")
    if report.get("preset"):
        lines.append(f"- Preset: {report['preset']}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Preview or create the reusable Forge workspace skeleton.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument(
        "--forge-home",
        type=Path,
        default=None,
        help="Override adapter state root (defaults to $FORGE_HOME, installed adapter state, bundle-native dev state, or ~/.forge only when no bundle-specific fallback exists)",
    )
    parser.add_argument("--project-name", default=None, help="Optional project name to seed into session metadata")
    parser.add_argument("--mode", choices=["auto", "greenfield", "existing"], default="auto", help="Override workspace classification")
    parser.add_argument("--preset", default=None, help="Optional companion preset such as nextjs-typescript-postgres/minimal-saas")
    parser.add_argument("--seed-preferences", action="store_true", help="Also create the adapter-global Forge preferences file with schema defaults")
    parser.add_argument("--seed-continuity", action="store_true", help="Also create empty decisions/learnings continuity files")
    parser.add_argument("--apply", action="store_true", help="Create the planned directories/files")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_plan(args)
    except (ValueError, RuntimeError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Workspace Init", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
