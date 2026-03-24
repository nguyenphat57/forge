from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, slugify


PATTERN_PROFILES = {
    "sync-api": {
        "objective": "Lock contract, validation, authorization, and compatibility before changing a synchronous API surface.",
        "focus": [
            "Define request, response, and error shapes explicitly.",
            "Preserve backward compatibility or document the breaking edge clearly.",
            "Map validation, authorization, and persistence boundaries before implementation.",
        ],
        "watchouts": [
            "Do not hide business logic inside handlers/controllers.",
            "Do not change response shape without updating callers and docs together.",
        ],
        "deliverables": [
            "Updated contract and handler/service implementation",
            "Verification notes for callers, auth, and persistence changes",
        ],
    },
    "async-job": {
        "objective": "Clarify ownership, retries, idempotency, and failure handling before changing a worker or queued flow.",
        "focus": [
            "Define enqueue, processing, retry, and dead-letter behavior.",
            "Make idempotency and partial-failure handling explicit.",
            "Document which side effects are atomic and which are compensating.",
        ],
        "watchouts": [
            "Do not assume retries are harmless without idempotency.",
            "Do not mix state changes and side effects without a recovery story.",
        ],
        "deliverables": [
            "Updated job/worker contract and processing notes",
            "Verification notes for retries, replay safety, and failure visibility",
        ],
    },
    "event-flow": {
        "objective": "Define event shape, ordering assumptions, and consumer impact before changing an event-driven flow.",
        "focus": [
            "Make event schema and versioning expectations explicit.",
            "Document ordering, replay, and dedup assumptions.",
            "List producers and consumers touched by the change.",
        ],
        "watchouts": [
            "Do not treat event payloads as private if multiple consumers exist.",
            "Do not change ordering assumptions without naming the blast radius.",
        ],
        "deliverables": [
            "Updated event contract and producer/consumer notes",
            "Verification notes for replay, duplicates, and downstream compatibility",
        ],
    },
    "data-change": {
        "objective": "Clarify schema evolution, migration safety, and data backfill behavior before changing a data model.",
        "focus": [
            "Prefer expand-contract or equivalent safe evolution where possible.",
            "Name migration steps, backfill plan, and rollback posture.",
            "List callers, reports, or jobs that rely on the old shape.",
        ],
        "watchouts": [
            "Do not ship destructive schema changes without a compatibility window.",
            "Do not assume migration success without data-volume and lock-time thought.",
        ],
        "deliverables": [
            "Migration plan and schema notes",
            "Verification notes for backfill, compatibility, and rollback risk",
        ],
    },
}


RUNTIME_PROFILES = {
    "generic": [
        "Keep contracts explicit even when the runtime is dynamic.",
        "Prefer boundary validation, typed envelopes, and replay-safe side effects.",
    ],
    "node-service": [
        "Separate transport, service, and persistence concerns; avoid controller bloat.",
        "Watch async error propagation, retry loops, and hidden shared state.",
    ],
    "python-service": [
        "Keep schema validation and serialization explicit; avoid duck-typed surprises at the boundary.",
        "Make task re-entry, transaction scope, and dependency lifetimes obvious.",
    ],
    "go-service": [
        "Keep interfaces small and error handling explicit.",
        "Treat context propagation, cancellation, and retries as part of the contract.",
    ],
    "java-service": [
        "Keep transaction boundaries visible and do not hide behavior behind annotations alone.",
        "Be explicit about DTO/domain mapping and persistence side effects.",
    ],
    "dotnet-service": [
        "Keep request pipeline, domain logic, and data access separate.",
        "Be explicit about async flows, cancellation tokens, and serialization contracts.",
    ],
}


COMMON_SECTIONS = [
    "Contract or surface in scope",
    "Validation and authorization boundary",
    "Data model, migration, or persistence impact",
    "Consistency, idempotency, retry, or replay behavior",
    "Observability and operational notes",
    "Caller, consumer, or downstream compatibility",
]


def build_brief(args: argparse.Namespace) -> dict:
    profile = PATTERN_PROFILES[args.pattern]
    runtime_focus = RUNTIME_PROFILES[args.runtime]
    project_name = args.project_name or Path.cwd().name
    return {
        "title": "Backend Brief",
        "project_name": project_name,
        "surface": args.surface,
        "summary": args.summary,
        "pattern": args.pattern,
        "runtime": args.runtime,
        "objective": profile["objective"],
        "sections": COMMON_SECTIONS,
        "pattern_focus": profile["focus"],
        "pattern_watchouts": profile["watchouts"],
        "runtime_focus": runtime_focus,
        "deliverables": profile["deliverables"],
        "notes": args.note,
    }


def format_markdown(brief: dict) -> str:
    surface_label = brief["surface"] or "shared"
    lines = [
        f"# {brief['title']}: {surface_label}",
        "",
        f"- Project: {brief['project_name']}",
        f"- Surface: {surface_label}",
        f"- Pattern: {brief['pattern']}",
        f"- Runtime: {brief['runtime']}",
        "",
        "## Summary",
        brief["summary"],
        "",
        "## Objective",
        brief["objective"],
        "",
        "## Required Sections",
    ]
    for item in brief["sections"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Pattern Focus",
    ])
    for item in brief["pattern_focus"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Runtime Focus",
    ])
    for item in brief["runtime_focus"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Anti-Patterns To Reject",
    ])
    for item in brief["pattern_watchouts"]:
        lines.append(f"- {item}")

    if brief["notes"]:
        lines.extend([
            "",
            "## Notes",
        ])
        for item in brief["notes"]:
            lines.append(f"- {item}")

    lines.extend([
        "",
        "## Expected Deliverables",
    ])
    for item in brief["deliverables"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Review Prompts",
        "- Which callers or consumers break first if this contract changes?",
        "- Where would replay, retry, or partial failure hurt the most?",
        "- What migration or compatibility step is easiest to forget?",
        "- What evidence proves this change is safe beyond the happy path?",
    ])
    return "\n".join(lines) + "\n"


def format_override_markdown(brief: dict) -> str:
    surface_label = brief["surface"] or "shared"
    lines = [
        f"# Surface Override: {surface_label}",
        "",
        f"- Project: {brief['project_name']}",
        f"- Pattern: {brief['pattern']}",
        f"- Runtime: {brief['runtime']}",
        "",
        "Use this file only for surface-specific differences. `MASTER.md` stays the baseline source of truth.",
        "",
        "## Scope Override",
        brief["summary"],
        "",
        "## Contract Notes",
        "- Capture only the contract or caller details that differ from the master brief.",
        "",
        "## Data / Consistency Notes",
        "- Call out migration, idempotency, replay, or transaction notes unique to this surface.",
        "",
        "## Ops Notes",
        "- Call out observability, alerts, auth, or rollback details unique to this surface.",
    ]
    if brief["notes"]:
        lines.extend([
            "",
            "## Extra Notes",
        ])
        for item in brief["notes"]:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def persist_brief(brief: dict, output_dir: str | None) -> list[Path]:
    artifact_root = default_artifact_dir(output_dir, "backend-briefs") / slugify(brief["project_name"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    master_md = artifact_root / "MASTER.md"
    master_json = artifact_root / "MASTER.json"
    master_md.write_text(format_markdown(brief), encoding="utf-8")
    master_json.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    written.extend([master_md, master_json])

    if brief["surface"]:
        surfaces_dir = artifact_root / "surfaces"
        surfaces_dir.mkdir(parents=True, exist_ok=True)
        override_path = surfaces_dir / f"{slugify(brief['surface'])}.md"
        override_path.write_text(format_override_markdown(brief), encoding="utf-8")
        written.append(override_path)

    return written


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Generate a backend brief artifact.")
    parser.add_argument("summary", help="Task summary or backend change statement")
    parser.add_argument("--project-name", default=None, help="Project name for persisted artifacts")
    parser.add_argument("--surface", default=None, help="Optional endpoint/job/event/surface name")
    parser.add_argument(
        "--pattern",
        choices=sorted(PATTERN_PROFILES.keys()),
        default="sync-api",
        help="Backend change pattern to apply",
    )
    parser.add_argument(
        "--runtime",
        choices=sorted(RUNTIME_PROFILES.keys()),
        default="generic",
        help="Runtime lens to apply",
    )
    parser.add_argument("--note", action="append", default=[], help="Extra note to include. Repeatable.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist to .forge-artifacts/backend-briefs/<project>/")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    brief = build_brief(args)
    if args.format == "json":
        print(json.dumps(brief, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(brief))

    if args.persist:
        written = persist_brief(brief, args.output_dir)
        print("\nPersisted backend brief artifacts:")
        for path in written:
            print(f"- {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
