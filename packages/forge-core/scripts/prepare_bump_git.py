from __future__ import annotations

import subprocess
from pathlib import Path


CAPABILITY_PATH_HINTS = ("workflows/", "scripts/", "commands/", "skills/", "domains/", "data/")
PUBLIC_SURFACE_PATH_HINTS = (
    "api/",
    "public/",
    "sdk/",
    "openapi",
    "swagger",
    "schema",
    "migrations/",
    "contracts/",
)
DOC_PATH_HINTS = ("docs/", "references/")
TEST_PATH_HINTS = ("tests/", "test/", "__tests__/")
RELEASE_ARTIFACTS = {"VERSION", "CHANGELOG.md"}
BREAKING_TEXT_HINTS = (
    "breaking change",
    "breaking:",
    "incompatible",
    "drop column",
    "drop table",
    "remove support",
    "requires migration",
)


def run_git_command(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def is_git_workspace(workspace: Path) -> bool:
    completed = run_git_command(workspace, "rev-parse", "--is-inside-work-tree")
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def normalize_repo_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def path_matches_hints(path: str, hints: tuple[str, ...]) -> bool:
    normalized = normalize_repo_path(path).strip("/")
    if not normalized:
        return False
    padded = f"/{normalized}/"
    for hint in hints:
        token = normalize_repo_path(hint).strip("/")
        if not token:
            continue
        if f"/{token}/" in padded:
            return True
        if token in normalized and "/" not in token:
            return True
    return False


def parse_name_status(output: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = raw_line.split("\t")
        status = parts[0]
        kind = status[0]
        if kind == "R" and len(parts) >= 3:
            path = parts[2]
            original = parts[1]
        elif len(parts) >= 2:
            path = parts[1]
            original = ""
        else:
            continue
        entries.append(
            {
                "status": kind,
                "path": normalize_repo_path(path),
                "original_path": normalize_repo_path(original) if original else "",
            }
        )
    return entries


def parse_status_porcelain(output: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for raw_line in output.splitlines():
        if len(raw_line) < 4:
            continue
        status = raw_line[:2]
        path_text = raw_line[3:]
        current_path = path_text.split(" -> ", 1)[-1]
        entries.append(
            {
                "status": "?" if status == "??" else status.strip()[:1],
                "path": normalize_repo_path(current_path),
                "original_path": "",
            }
        )
    return entries


def dedupe_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for entry in entries:
        path = entry["path"]
        existing = merged.get(path)
        if existing is None or existing["status"] == "M":
            merged[path] = entry
    return [merged[path] for path in sorted(merged)]


def resolve_release_base_commit(workspace: Path) -> str | None:
    completed = run_git_command(workspace, "log", "-n", "1", "--format=%H", "--", "VERSION")
    if completed.returncode != 0:
        return None
    commit = completed.stdout.strip()
    return commit or None


def collect_release_diff(workspace: Path) -> tuple[list[dict[str, str]], str, str, list[str]]:
    warnings: list[str] = []
    if not is_git_workspace(workspace):
        return [], "", "no-git-context", ["Git context unavailable; semver inference falls back to conservative heuristics."]

    base_commit = resolve_release_base_commit(workspace)
    entries: list[dict[str, str]] = []
    diff_text = ""

    if base_commit:
        name_status = run_git_command(workspace, "diff", "--name-status", base_commit, "--", ".")
        if name_status.returncode == 0:
            entries.extend(parse_name_status(name_status.stdout))
        diff_completed = run_git_command(workspace, "diff", base_commit, "--", ".")
        if diff_completed.returncode == 0:
            diff_text = diff_completed.stdout
        scope = "since-last-version-change"
    else:
        warnings.append("Could not find a prior commit touching VERSION; using working tree only.")
        scope = "working-tree-only"

    porcelain = run_git_command(workspace, "status", "--porcelain=v1", "--untracked-files=all", "--", ".")
    if porcelain.returncode == 0:
        entries.extend(parse_status_porcelain(porcelain.stdout))
    else:
        warnings.append("Could not read git status; inference may miss untracked files.")

    return dedupe_entries(entries), diff_text.casefold(), scope, warnings


def is_release_artifact(path: str) -> bool:
    return normalize_repo_path(path) in RELEASE_ARTIFACTS


def is_doc_or_test_path(path: str) -> bool:
    normalized = normalize_repo_path(path)
    if path_matches_hints(normalized, CAPABILITY_PATH_HINTS):
        return False
    if path_matches_hints(normalized, DOC_PATH_HINTS) or path_matches_hints(normalized, TEST_PATH_HINTS):
        return True
    if normalized.endswith((".md", ".rst", ".txt")) and "/" not in normalized:
        return True
    return normalized.endswith((".md", ".rst", ".txt")) and not path_matches_hints(normalized, ("src", "lib", "api", "public", "sdk"))


def infer_bump_token(workspace: Path) -> tuple[str, str, list[str], list[str], list[str]]:
    entries, diff_text, analysis_scope, warnings = collect_release_diff(workspace)
    changed_paths = [entry["path"] for entry in entries if not is_release_artifact(entry["path"])]

    if not changed_paths:
        warnings.append("No code or product-facing changes detected beyond release artifacts.")
        return (
            "patch",
            analysis_scope,
            ["No diff was detected since the last VERSION change; defaulting to a patch bump."],
            changed_paths,
            warnings,
        )

    breaking_paths = [path for path in changed_paths if path_matches_hints(path, PUBLIC_SURFACE_PATH_HINTS)]
    if breaking_paths and any(hint in diff_text for hint in BREAKING_TEXT_HINTS):
        return (
            "major",
            analysis_scope,
            [
                "Public surface files changed and the diff contains explicit breaking-change signals.",
                f"Breaking-sensitive paths: {', '.join(breaking_paths[:3])}",
            ],
            changed_paths,
            warnings,
        )

    new_capability_paths = [
        entry["path"]
        for entry in entries
        if entry["status"] in {"A", "R", "?"}
        and not is_release_artifact(entry["path"])
        and not is_doc_or_test_path(entry["path"])
    ]
    if new_capability_paths:
        return (
            "minor",
            analysis_scope,
            [
                "New non-doc files were added since the last VERSION change, which usually indicates new capability.",
                f"Examples: {', '.join(new_capability_paths[:3])}",
            ],
            changed_paths,
            warnings,
        )

    capability_path_changes = [
        path
        for path in changed_paths
        if path_matches_hints(path, CAPABILITY_PATH_HINTS) or path_matches_hints(path, PUBLIC_SURFACE_PATH_HINTS)
    ]
    if capability_path_changes:
        return (
            "minor",
            analysis_scope,
            [
                "Capability-bearing workflow/script/data/public-surface files changed.",
                f"Examples: {', '.join(capability_path_changes[:3])}",
            ],
            changed_paths,
            warnings,
        )

    product_code_paths = [path for path in changed_paths if not is_doc_or_test_path(path)]
    if product_code_paths:
        return (
            "patch",
            analysis_scope,
            [
                "Existing implementation files changed without strong signals for a new public capability or breaking change.",
                f"Examples: {', '.join(product_code_paths[:3])}",
            ],
            changed_paths,
            warnings,
        )

    warnings.append("Only docs/tests/release-support files changed; patch is a conservative default.")
    return (
        "patch",
        analysis_scope,
        ["Only docs/tests/supporting files changed since the last VERSION change."],
        changed_paths,
        warnings,
    )


def infer_confidence(bump_token: str, warnings: list[str], reasons: list[str], analysis_scope: str) -> str:
    if bump_token == "major":
        return "high"
    if bump_token == "minor" and analysis_scope == "since-last-version-change":
        return "high"
    if bump_token == "minor":
        return "medium"
    if warnings:
        return "low"
    if reasons:
        return "medium"
    return "low"
