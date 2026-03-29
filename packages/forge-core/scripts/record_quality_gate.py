from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify, timestamp_slug
from workflow_state_support import record_workflow_event


VALID_PROFILES = (
    "standard",
    "release-critical",
    "migration-critical",
    "external-interface",
    "regression-recovery",
)
VALID_TARGET_CLAIMS = ("done", "ready-for-review", "ready-for-merge", "deploy")
VALID_DECISIONS = ("go", "conditional", "blocked")
TARGETS_REQUIRING_PROCESS_ARTIFACT = set(VALID_TARGET_CLAIMS)
TARGETS_REQUIRING_REVIEW_ARTIFACT = {"ready-for-merge", "done", "deploy"}


def _mtime_rank(path: Path | None) -> tuple[float, str]:
    if path is None:
        return float("-inf"), ""
    try:
        return path.stat().st_mtime, str(path).lower()
    except OSError:
        return float("-inf"), ""


def _pick_latest_json(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob("*.json"):
        rank = _mtime_rank(candidate)
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def _pick_latest_named(base_dir: Path, filename: str) -> Path | None:
    if not base_dir.exists():
        return None
    latest_path: Path | None = None
    latest_rank = (float("-inf"), "")
    for candidate in base_dir.rglob(filename):
        rank = _mtime_rank(candidate)
        if rank > latest_rank:
            latest_path = candidate
            latest_rank = rank
    return latest_path


def _read_json_object(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _artifact_ref(kind: str, path: Path, payload: dict, *, summary_key: str, state_key: str) -> dict:
    return {
        "kind": kind,
        "path": str(path),
        "summary": payload.get(summary_key),
        "state": payload.get(state_key),
    }


def _collect_process_artifacts(workspace: Path) -> tuple[list[dict], dict | None]:
    artifacts: list[dict] = []
    latest_execution: dict | None = None

    change_path = _pick_latest_named(workspace / ".forge-artifacts" / "changes" / "active", "status.json")
    change_payload = _read_json_object(change_path)
    if change_path is not None and isinstance(change_payload, dict):
        artifacts.append(_artifact_ref("change-state", change_path, change_payload, summary_key="summary", state_key="state"))

    execution_path = _pick_latest_json(workspace / ".forge-artifacts" / "execution-progress")
    execution_payload = _read_json_object(execution_path)
    if execution_path is not None and isinstance(execution_payload, dict):
        latest_execution = execution_payload
        artifacts.append(
            _artifact_ref(
                "execution-progress",
                execution_path,
                execution_payload,
                summary_key="task",
                state_key="completion_state",
            )
        )

    return artifacts, latest_execution


def _collect_review_artifacts(workspace: Path) -> tuple[list[dict], tuple[str, dict, Path] | None]:
    candidates: list[tuple[str, dict, Path]] = []
    review_state_path = _pick_latest_json(workspace / ".forge-artifacts" / "reviews")
    review_state_payload = _read_json_object(review_state_path)
    if review_state_path is not None and isinstance(review_state_payload, dict):
        candidates.append(("review-state", review_state_payload, review_state_path))

    review_pack_path = _pick_latest_json(workspace / ".forge-artifacts" / "review-packs")
    review_pack_payload = _read_json_object(review_pack_path)
    if review_pack_path is not None and isinstance(review_pack_payload, dict):
        candidates.append(("review-pack", review_pack_payload, review_pack_path))

    refs: list[dict] = []
    for kind, payload, path in candidates:
        if kind == "review-state":
            refs.append(_artifact_ref(kind, path, payload, summary_key="scope", state_key="disposition"))
        else:
            refs.append(_artifact_ref(kind, path, payload, summary_key="summary", state_key="status"))

    if not candidates:
        return refs, None

    latest_kind, latest_payload, latest_path = max(candidates, key=lambda item: _mtime_rank(item[2]))
    return refs, (latest_kind, latest_payload, latest_path)


def _validate_supporting_artifacts(args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    workspace = args.workspace.resolve()
    process_artifacts, latest_execution = _collect_process_artifacts(workspace)
    if args.target_claim in TARGETS_REQUIRING_PROCESS_ARTIFACT and not process_artifacts:
        raise ValueError(
            f"Quality gate requires an active change or execution-progress artifact before claiming '{args.target_claim}'."
        )

    if (
        args.target_claim in TARGETS_REQUIRING_PROCESS_ARTIFACT
        and isinstance(latest_execution, dict)
        and latest_execution.get("harness_available") == "yes"
        and not latest_execution.get("red_proof")
    ):
        raise ValueError("Harness-backed readiness claims require persisted RED proof in execution-progress.")

    review_artifacts: list[dict] = []
    if args.decision == "go" and args.target_claim in TARGETS_REQUIRING_REVIEW_ARTIFACT:
        review_artifacts, latest_review = _collect_review_artifacts(workspace)
        if latest_review is None:
            raise ValueError(
                f"Go decision for '{args.target_claim}' requires a persisted review-state or review-pack artifact."
            )
        latest_kind, latest_payload, _ = latest_review
        if latest_kind == "review-state" and latest_payload.get("disposition") != "ready-for-merge":
            raise ValueError(
                f"Latest review-state must be 'ready-for-merge' before claiming '{args.target_claim}'."
            )
        if latest_kind == "review-pack" and latest_payload.get("status") != "PASS":
            raise ValueError(
                f"Latest review-pack must be PASS before claiming '{args.target_claim}'."
            )

    return process_artifacts, review_artifacts


def build_report(args: argparse.Namespace) -> dict:
    if not args.evidence:
        raise ValueError("Quality gate requires at least one fresh evidence item.")
    if args.decision in {"conditional", "blocked"} and not args.next_evidence:
        raise ValueError("Conditional or blocked decisions must name the next evidence needed.")
    if args.profile == "release-critical" and args.target_claim == "deploy" and args.decision == "conditional":
        raise ValueError("release-critical deploy gates cannot be conditional.")

    status = {"go": "PASS", "conditional": "WARN", "blocked": "FAIL"}[args.decision]
    workspace = args.workspace.resolve()
    process_artifacts, review_artifacts = _validate_supporting_artifacts(args)
    return {
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": args.project_name,
        "workspace": str(workspace),
        "profile": args.profile,
        "target_claim": args.target_claim,
        "decision": args.decision,
        "evidence_read": args.evidence,
        "response": args.response,
        "why": args.why,
        "next_evidence": args.next_evidence,
        "risks": args.risk,
        "process_artifacts": process_artifacts,
        "review_artifacts": review_artifacts,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Quality Gate",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Project: {report['project']}",
        f"- Profile: {report['profile']}",
        f"- Target claim: {report['target_claim']}",
        f"- Decision: {report['decision']}",
        f"- Evidence response: {report['response']}",
        f"- Why: {report['why']}",
    ]
    for label, items in (("Evidence read", report["evidence_read"]), ("Next evidence needed", report["next_evidence"]), ("Risks", report["risks"])):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {label}: (none)")
    for label, items in (("Process artifacts", report.get("process_artifacts", [])), ("Review artifacts", report.get("review_artifacts", []))):
        if items:
            lines.append(f"- {label}:")
            for item in items:
                lines.append(f"  - {item['kind']}: {item.get('summary') or '(none)'} | {item['path']}")
        else:
            lines.append(f"- {label}: (none)")
    artifacts = report.get("artifacts")
    if artifacts:
        lines.append("- Artifacts:")
        lines.append(f"  - JSON: {artifacts['json']}")
        lines.append(f"  - Markdown: {artifacts['markdown']}")
    return "\n".join(lines)


def persist_report(report: dict, output_dir: str | None) -> tuple[Path, Path]:
    artifact_dir = default_artifact_dir(output_dir, "quality-gates") / slugify(report["project"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp_slug()}-{report['decision']}-{slugify(report['target_claim'])}"
    json_path = artifact_dir / f"{stem}.json"
    md_path = artifact_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(format_text(report), encoding="utf-8")
    record_workflow_event("quality-gate", report, output_dir=output_dir, source_path=json_path)
    return json_path, md_path


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Record an explicit Forge quality-gate decision from fresh evidence.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root the gate applies to")
    parser.add_argument("--project-name", default="workspace", help="Project or workspace name for workflow-state grouping")
    parser.add_argument("--profile", required=True, choices=VALID_PROFILES, help="Quality-gate profile")
    parser.add_argument("--target-claim", required=True, choices=VALID_TARGET_CLAIMS, help="Claim being gated")
    parser.add_argument("--decision", required=True, choices=VALID_DECISIONS, help="Gate decision")
    parser.add_argument("--evidence", action="append", default=[], help="Fresh evidence item. Repeatable.")
    parser.add_argument("--response", required=True, help="Evidence response line that follows the gate contract")
    parser.add_argument("--why", required=True, help="Reason for the current gate decision")
    parser.add_argument("--next-evidence", action="append", default=[], help="Next evidence needed before the gate can improve")
    parser.add_argument("--risk", action="append", default=[], help="Residual risk note. Repeatable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist the decision under .forge-artifacts/quality-gates")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except ValueError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Quality Gate", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.persist:
        json_path, md_path = persist_report(report, args.output_dir)
        report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
