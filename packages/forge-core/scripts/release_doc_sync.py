from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio, default_artifact_dir, timestamp_slug
from help_next_support import read_git_status


DOC_CATEGORIES = {
    "readme": ("README", "README.md"),
    "architecture": ("docs/architecture/",),
    "release": ("CHANGELOG.md", "docs/release/"),
    "planning": ("docs/plans/", "docs/specs/"),
}

CHANGE_RULES = (
    {
        "id": "product-surface",
        "match_prefixes": ("app/", "src/", "api/", "pages/", "components/"),
        "required_doc_categories": ("readme", "architecture", "planning"),
        "reason": "Product surface changed.",
    },
    {
        "id": "database-surface",
        "match_prefixes": ("prisma/", "migrations/", "supabase/migrations/"),
        "required_doc_categories": ("architecture", "release"),
        "reason": "Database or migration surface changed.",
    },
    {
        "id": "config-surface",
        "match_names": (
            "package.json",
            "pyproject.toml",
            ".env.example",
            "wrangler.toml",
            "next.config.ts",
            "vite.config.ts",
            "capacitor.config.ts",
        ),
        "required_doc_categories": ("readme", "release"),
        "reason": "Runtime or release config changed.",
    },
    {
        "id": "auth-surface",
        "match_prefixes": ("app/(auth)/", "lib/auth/"),
        "match_names": ("middleware.ts", "auth.config.ts"),
        "required_doc_categories": ("readme", "architecture", "planning"),
        "reason": "Auth or route protection surface changed.",
    },
    {
        "id": "billing-surface",
        "match_prefixes": ("app/(app)/billing/", "app/api/webhooks/stripe/", "lib/billing/"),
        "required_doc_categories": ("architecture", "release", "planning"),
        "reason": "Billing or webhook surface changed.",
    },
    {
        "id": "observability-surface",
        "match_prefixes": ("app/api/health/", "app/api/ready/"),
        "match_names": ("instrumentation.ts", "sentry.client.config.ts", "sentry.server.config.ts", "sentry.edge.config.ts"),
        "required_doc_categories": ("architecture", "release"),
        "reason": "Observability or health surface changed.",
    },
)


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _doc_categories(changed_paths: list[str]) -> set[str]:
    categories: set[str] = set()
    for path in changed_paths:
        normalized = _normalize(path)
        for category, markers in DOC_CATEGORIES.items():
            if any(normalized == marker or normalized.startswith(marker) for marker in markers):
                categories.add(category)
    return categories


def _required_updates(changed_paths: list[str], docs_touched: set[str]) -> list[dict]:
    requirements: list[dict] = []
    normalized_paths = [_normalize(path) for path in changed_paths]
    for rule in CHANGE_RULES:
        matched = any(
            any(path.startswith(prefix) for prefix in rule.get("match_prefixes", ()))
            or path in rule.get("match_names", ())
            for path in normalized_paths
        )
        if not matched:
            continue
        matched_paths = [
            path
            for path in normalized_paths
            if any(path.startswith(prefix) for prefix in rule.get("match_prefixes", ())) or path in rule.get("match_names", ())
        ]
        satisfied = any(category in docs_touched for category in rule["required_doc_categories"])
        requirements.append(
            {
                "id": rule["id"],
                "reason": rule["reason"],
                "required_doc_categories": list(rule["required_doc_categories"]),
                "matched_paths": matched_paths,
                "satisfied": satisfied,
            }
        )
    return requirements


def build_report(workspace: Path, changed_paths: list[str]) -> dict:
    docs_touched = _doc_categories(changed_paths)
    requirements = _required_updates(changed_paths, docs_touched)
    warnings = [
        "Missing doc coverage for {rule}: {reason} Required one of [{categories}].".format(
            rule=item["id"],
            reason=item["reason"],
            categories=", ".join(item["required_doc_categories"]),
        )
        for item in requirements
        if not item["satisfied"]
    ]
    status = "PASS" if not warnings else "WARN"
    summary = "Docs look aligned with the changed release surface." if status == "PASS" else "Release-doc drift likely needs follow-up."
    suggestions = sorted({category for item in requirements if not item["satisfied"] for category in item["required_doc_categories"]})
    coverage_gaps = [
        {"rule": item["id"], "reason": item["reason"], "matched_paths": item["matched_paths"], "suggested_categories": item["required_doc_categories"]}
        for item in requirements
        if not item["satisfied"]
    ]
    return {
        "status": status,
        "workspace": str(workspace),
        "changed_paths": changed_paths,
        "docs_touched": sorted(docs_touched),
        "requirements": requirements,
        "matched_rules": [item["id"] for item in requirements],
        "coverage_gaps": coverage_gaps,
        "summary": summary,
        "warnings": warnings,
        "suggested_doc_updates": suggestions,
    }


def persist_report(report: dict, output_dir: str | None) -> dict[str, str]:
    artifact_dir = default_artifact_dir(output_dir, "release-doc-sync")
    history_dir = artifact_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stamp = timestamp_slug()
    latest_json = artifact_dir / "latest.json"
    latest_md = artifact_dir / "latest.md"
    history_json = history_dir / f"{stamp}.json"
    history_md = history_dir / f"{stamp}.md"
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    markdown = format_text(report)
    for path in (latest_json, history_json):
        path.write_text(payload, encoding="utf-8")
    for path in (latest_md, history_md):
        path.write_text(markdown, encoding="utf-8")
    return {"json": str(latest_json), "markdown": str(latest_md)}


def format_text(report: dict) -> str:
    lines = [
        "Forge Release-Doc Sync",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Summary: {report['summary']}",
        f"- Docs touched: {', '.join(report['docs_touched']) or '(none)'}",
        "- Changed paths:",
    ]
    for item in report["changed_paths"] or ["(none)"]:
        lines.append(f"  - {item}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    if report["coverage_gaps"]:
        lines.append("- Coverage gaps:")
        for item in report["coverage_gaps"]:
            lines.append(f"  - {item['rule']}: {', '.join(item['suggested_categories'])}")
    lines.append(f"- Suggested doc updates: {', '.join(report['suggested_doc_updates']) or '(none)'}")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Check whether release-facing docs stayed aligned with changed code surfaces.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--changed-path", action="append", default=[], help="Explicit changed path. Repeatable.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--persist", action="store_true", help="Persist report under .forge-artifacts/release-doc-sync")
    parser.add_argument("--output-dir", default=None, help="Base directory for persisted artifacts")
    args = parser.parse_args()

    changed_paths = [_normalize(path) for path in args.changed_path]
    if not changed_paths:
        git_state = read_git_status(args.workspace.resolve())
        changed_paths = sorted({*git_state["changed_files"], *git_state["untracked_files"]})
    report = build_report(args.workspace.resolve(), changed_paths)
    if args.persist:
        report["artifacts"] = persist_report(report, args.output_dir or str(args.workspace.resolve()))

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
