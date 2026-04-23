from __future__ import annotations

from _forge_skill_command import bootstrap_command_paths

bootstrap_command_paths()

import argparse
import json
import subprocess
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug


def _run(command: str, cwd: Path) -> dict:
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def _detect_repo_root(workspace: Path) -> Path:
    result = _run_git(["git", "rev-parse", "--show-toplevel"], workspace)
    if result.returncode != 0:
        raise ValueError("prepare-worktree requires a git repository with at least one commit.")
    return Path(result.stdout.strip()).resolve()


def _ensure_ignore_safety(workspace: Path, repo_root: Path, worktree_root: Path) -> dict:
    try:
        relative_root = worktree_root.resolve().relative_to(workspace.resolve())
    except ValueError:
        return {"required": False, "applied": False, "pattern": None, "path": None}
    pattern = f"/{relative_root.as_posix()}/"
    exclude_path = repo_root / ".git" / "info" / "exclude"
    current = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    applied = False
    if pattern not in current:
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "\n" if current and not current.endswith("\n") else ""
        exclude_path.write_text(f"{current}{prefix}{pattern}\n", encoding="utf-8")
        applied = True
    return {"required": True, "applied": applied, "pattern": pattern, "path": str(exclude_path)}


def _create_or_reuse_worktree(repo_root: Path, worktree_path: Path) -> dict:
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    if worktree_path.exists() and any(worktree_path.iterdir()):
        return {"action": "reused", "command": None, "returncode": 0, "stdout": "", "stderr": ""}
    result = _run_git(["git", "worktree", "add", "--detach", str(worktree_path), "HEAD"], repo_root)
    return {
        "action": "created" if result.returncode == 0 else "failed",
        "command": "git worktree add --detach <path> HEAD",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build_report(args: argparse.Namespace) -> dict:
    if not args.baseline_command:
        raise ValueError("prepare-worktree requires at least one --baseline-command.")

    workspace = args.workspace.resolve()
    repo_root = _detect_repo_root(workspace)
    worktree_root = args.worktree_root.resolve() if args.worktree_root else workspace / ".forge-artifacts" / "worktrees"
    worktree_path = worktree_root / slugify(args.name or workspace.name)
    ignore_safety = _ensure_ignore_safety(workspace, repo_root, worktree_root)
    worktree_action = _create_or_reuse_worktree(repo_root, worktree_path)
    if worktree_action["returncode"] != 0:
        return {
            "status": "FAIL",
            "state": "blocked",
            "workspace": str(workspace),
            "repo_root": str(repo_root),
            "worktree_root": str(worktree_root),
            "worktree_path": str(worktree_path),
            "ignore_safety": ignore_safety,
            "worktree_action": worktree_action,
            "setup_results": [],
            "baseline_results": [],
        }

    setup_results = [_run(command, worktree_path) for command in args.setup_command]
    baseline_results = [_run(command, worktree_path) for command in args.baseline_command] if all(item["returncode"] == 0 for item in setup_results) else []
    blocked = any(item["returncode"] != 0 for item in [*setup_results, *baseline_results])
    return {
        "status": "FAIL" if blocked else "PASS",
        "state": "blocked" if blocked else "ready",
        "workspace": str(workspace),
        "repo_root": str(repo_root),
        "worktree_root": str(worktree_root),
        "worktree_path": str(worktree_path),
        "ignore_safety": ignore_safety,
        "worktree_action": worktree_action,
        "setup_results": setup_results,
        "baseline_results": baseline_results,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Prepare Worktree",
        f"- Status: {report['status']}",
        f"- State: {report['state']}",
        f"- Workspace: {report['workspace']}",
        f"- Repo root: {report['repo_root']}",
        f"- Worktree path: {report['worktree_path']}",
        f"- Worktree action: {report['worktree_action']['action']}",
    ]
    ignore_safety = report["ignore_safety"]
    if ignore_safety["required"]:
        lines.append(
            f"- Ignore safety: {ignore_safety['pattern']} -> {'applied' if ignore_safety['applied'] else 'already present'}"
        )
    else:
        lines.append("- Ignore safety: not required")
    for label, items in (("Setup results", report["setup_results"]), ("Baseline results", report["baseline_results"])):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - [{item['returncode']}] {item['command']}")
        else:
            lines.append(f"- {label}: (none)")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "worktree-prep") / slugify(Path(report["worktree_path"]).name)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{report['state']}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Prepare an isolated git worktree and baseline proof for risky Forge work.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--name", default=None, help="Worktree name or slug")
    parser.add_argument("--worktree-root", type=Path, default=None, help="Optional worktree root path")
    parser.add_argument("--setup-command", action="append", default=[], help="Optional setup command to run inside the worktree")
    parser.add_argument("--baseline-command", action="append", default=[], help="Baseline command to prove a clean start")
    parser.add_argument("--persist", action="store_true", help="Persist the worktree-prep artifact")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Prepare Worktree", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir or str(args.workspace.resolve()))
        report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
