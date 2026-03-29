from __future__ import annotations

import argparse
import json
from pathlib import Path

from change_artifacts_archive import archive_change
from change_artifacts_paths import resolve_change_paths
from change_artifacts_status import update_change_status
from change_guard import guard_change
from common import configure_stdio, slugify


def _start_change(workspace: Path, summary: str, slug: str | None, tasks: list[str], risks: list[str], verification: list[str]) -> dict:
    paths = resolve_change_paths(workspace, summary=summary, slug=slug)
    paths["active_root"].mkdir(parents=True, exist_ok=True)
    proposal = "\n".join(
        [
            "# Proposal",
            "",
            f"- Why: {summary}",
            "- Scope: medium or large work slice",
            "- Non-goals: expand scope without updating artifacts",
            "- Resume rule: keep the smallest coherent slice visible in the active artifacts.",
        ]
    )
    design = "\n".join(["# Design", "", "- Affected areas: confirm during implementation", "- Approach: update the smallest coherent slice first", "- Risks:", *[f"  - {item}" for item in (risks or ['Scope drift if artifacts are not updated.'])]])
    task_lines = tasks or ["Identify the first concrete slice before editing.", "Record the nearest verification command before implementation."]
    task_text = "\n".join(["# Tasks", "", *[f"- [ ] {item}" for item in task_lines]])
    verification_lines = verification or ["Verification method not recorded yet."]
    verification_text = "\n".join(["# Verification", "", *[f"- {item}" for item in verification_lines]])
    resume_text = "\n".join(
        [
            "# Resume",
            "",
            f"- Summary: {summary}",
            f"- Active slug: {slugify(slug or summary)}",
            f"- First step: {task_lines[0]}",
            f"- Verification: {verification_lines[0]}",
        ]
    )
    for path, content in ((paths["proposal"], proposal), (paths["design"], design), (paths["tasks"], task_text), (paths["verification"], verification_text)):
        path.write_text(content, encoding="utf-8")
    (paths["active_root"] / "resume.md").write_text(resume_text, encoding="utf-8")
    status = update_change_status(
        status_path=paths["status"],
        verification_path=paths["verification"],
        summary=summary,
        slug=slugify(slug or summary),
        state="proposed",
        note="Change created.",
        verified=None,
        residual_risk=[],
    )
    return {"status": "PASS", "workspace": str(workspace), "paths": {key: str(value) for key, value in paths.items()}, "change": status}


def _show_status(workspace: Path, slug: str, state: str | None, note: str | None, verified: str | None, residual_risk: list[str]) -> dict:
    paths = resolve_change_paths(workspace, slug=slug)
    if not paths["status"].exists():
        return {"status": "FAIL", "error": f"Unknown active change: {slug}"}
    payload = update_change_status(
        status_path=paths["status"],
        verification_path=paths["verification"],
        summary=json.loads(paths["status"].read_text(encoding="utf-8")).get("summary", slug),
        slug=slugify(slug),
        state=state,
        note=note,
        verified=verified,
        residual_risk=residual_risk,
    )
    return {"status": "PASS", "workspace": str(workspace), "change": payload, "status_path": str(paths["status"])}


def _archive(workspace: Path, slug: str, decision: list[str], learning: list[str]) -> dict:
    paths = resolve_change_paths(workspace, slug=slug)
    archived = archive_change(paths["active_root"], paths["archive_root"], decision=decision, learning=learning)
    return {"status": "PASS", "workspace": str(workspace), **archived}


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Create, update, archive, and guard Forge change artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("summary")
    start_parser.add_argument("--workspace", type=Path, default=Path.cwd())
    start_parser.add_argument("--slug")
    start_parser.add_argument("--task", action="append", default=[])
    start_parser.add_argument("--risk", action="append", default=[])
    start_parser.add_argument("--verification", action="append", default=[])
    start_parser.add_argument("--format", choices=["text", "json"], default="text")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--workspace", type=Path, default=Path.cwd())
    status_parser.add_argument("--slug", required=True)
    status_parser.add_argument("--state")
    status_parser.add_argument("--note")
    status_parser.add_argument("--verified")
    status_parser.add_argument("--residual-risk", action="append", default=[])
    status_parser.add_argument("--format", choices=["text", "json"], default="text")

    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("--workspace", type=Path, default=Path.cwd())
    archive_parser.add_argument("--slug", required=True)
    archive_parser.add_argument("--decision", action="append", default=[])
    archive_parser.add_argument("--learning", action="append", default=[])
    archive_parser.add_argument("--format", choices=["text", "json"], default="text")

    guard_parser = subparsers.add_parser("guard")
    guard_parser.add_argument("summary")
    guard_parser.add_argument("--action", action="append", default=[])
    guard_parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    if args.command == "start":
        payload = _start_change(args.workspace.resolve(), args.summary, args.slug, args.task, args.risk, args.verification)
    elif args.command == "status":
        payload = _show_status(args.workspace.resolve(), args.slug, args.state, args.note, args.verified, args.residual_risk)
    elif args.command == "archive":
        try:
            payload = _archive(args.workspace.resolve(), args.slug, args.decision, args.learning)
        except FileNotFoundError as exc:
            payload = {"status": "FAIL", "error": str(exc)}
    else:
        payload = guard_change(args.summary, args.action)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0 if payload.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
