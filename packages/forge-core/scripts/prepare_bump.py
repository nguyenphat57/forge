from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from common import configure_stdio


SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
EXPLICIT_BUMP_TOKENS = {"patch", "minor", "major"}
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


def parse_version(value: str) -> tuple[int, int, int]:
    match = SEMVER_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def format_version(parts: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in parts)


def bump_version(current: str, bump: str) -> str:
    major, minor, patch = parse_version(current)
    token = bump.strip().lower()
    if token == "patch":
        return format_version((major, minor, patch + 1))
    if token == "minor":
        return format_version((major, minor + 1, 0))
    if token == "major":
        return format_version((major + 1, 0, 0))
    parse_version(token)
    return token


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

    breaking_paths = [
        path for path in changed_paths if path_matches_hints(path, PUBLIC_SURFACE_PATH_HINTS)
    ]
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


def update_changelog_content(content: str, target_version: str) -> str:
    today = date.today().isoformat()
    heading = f"## {target_version} - {today}"
    if heading in content:
        return content

    lines = content.splitlines()
    insertion = [
        heading,
        "",
        "- Describe release changes.",
        "",
    ]
    if lines and lines[0].startswith("# "):
        new_lines = [lines[0], "", *insertion, *lines[1:]]
    else:
        new_lines = ["# Changelog", "", *insertion, *lines]
    return "\n".join(new_lines).rstrip() + "\n"


def detect_verify_command(workspace: Path) -> list[str]:
    if (workspace / "scripts" / "verify_repo.py").exists():
        return ["python", "scripts/verify_repo.py"]
    if (workspace / "scripts" / "verify_bundle.py").exists():
        return ["python", "scripts/verify_bundle.py"]
    return ["git", "diff", "--stat"]


def build_report(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    version_path = workspace / "VERSION"
    changelog_path = workspace / "CHANGELOG.md"
    if not version_path.exists():
        raise FileNotFoundError(f"Missing VERSION file: {version_path}")
    if not changelog_path.exists():
        raise FileNotFoundError(f"Missing CHANGELOG.md: {changelog_path}")

    current_version = version_path.read_text(encoding="utf-8").strip()
    parse_version(current_version)
    requested_bump = (args.bump or "auto").strip()
    bump_source = "explicit"
    inferred_from = None
    inference_reasons: list[str] = []
    inference_confidence = None
    analysis_changed_files: list[str] = []
    warnings: list[str] = []

    if not requested_bump or requested_bump.lower() == "auto":
        selected_bump, inferred_from, inference_reasons, analysis_changed_files, warnings = infer_bump_token(workspace)
        inference_confidence = infer_confidence(selected_bump, warnings, inference_reasons, inferred_from)
        bump_source = "inferred"
    else:
        selected_bump = requested_bump

    target_version = bump_version(current_version, selected_bump)
    changelog_preview = update_changelog_content(changelog_path.read_text(encoding="utf-8"), target_version)

    changed_files = ["VERSION", "CHANGELOG.md"]
    verification_commands = [["git", "diff", "--stat"]]
    verify_command = detect_verify_command(workspace)
    if verify_command != verification_commands[0]:
        verification_commands.append(verify_command)
    if args.release_ready and verify_command not in verification_commands:
        verification_commands.append(verify_command)

    if args.apply:
        version_path.write_text(f"{target_version}\n", encoding="utf-8")
        changelog_path.write_text(changelog_preview, encoding="utf-8")

    status = "PASS"
    if target_version == current_version:
        status = "WARN"
        warnings.append("Target version matches the current version.")
    if bump_source == "inferred" and inference_confidence == "low":
        status = "WARN"
        warnings.append("Inferred bump has low confidence; consider overriding with --bump patch|minor|major.")

    return {
        "status": status,
        "workspace": str(workspace),
        "current_version": current_version,
        "target_version": target_version,
        "bump": requested_bump or "auto",
        "selected_bump": selected_bump,
        "bump_source": bump_source,
        "inference_confidence": inference_confidence,
        "inferred_from": inferred_from,
        "inference_reasons": inference_reasons,
        "analysis_changed_files": analysis_changed_files,
        "applied": args.apply,
        "changed_files": changed_files,
        "verification_commands": [" ".join(command) for command in verification_commands],
        "warnings": warnings,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Bump Preparation",
        f"- Status: {report['status']}",
        f"- Workspace: {report['workspace']}",
        f"- Version: {report['current_version']} -> {report['target_version']}",
        f"- Bump source: {report['bump_source']}",
        f"- Selected bump: {report['selected_bump']}",
        f"- Applied: {'yes' if report['applied'] else 'no'}",
        "- Changed files:",
    ]
    for item in report["changed_files"]:
        lines.append(f"  - {item}")
    lines.append("- Verification commands:")
    for item in report["verification_commands"]:
        lines.append(f"  - {item}")
    if report["inference_reasons"]:
        lines.append("- Inference reasons:")
        for item in report["inference_reasons"]:
            lines.append(f"  - {item}")
    if report["analysis_changed_files"]:
        lines.append("- Analysis changed files:")
        for item in report["analysis_changed_files"][:10]:
            lines.append(f"  - {item}")
    if report["inference_confidence"]:
        lines.append(f"- Inference confidence: {report['inference_confidence']}")
    if report["inferred_from"]:
        lines.append(f"- Inferred from: {report['inferred_from']}")
    if report["warnings"]:
        lines.append("- Warnings:")
        for item in report["warnings"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Warnings: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Prepare or apply a host-neutral version bump checklist.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root containing VERSION and CHANGELOG.md")
    parser.add_argument("--bump", default="auto", help="patch, minor, major, auto, or an explicit semantic version")
    parser.add_argument("--apply", action="store_true", help="Write VERSION and CHANGELOG.md instead of previewing only")
    parser.add_argument("--release-ready", action="store_true", help="Surface the nearest release verification command")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        report = build_report(args)
    except (FileNotFoundError, ValueError) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("\n".join(["Forge Bump Preparation", "- Status: FAIL", f"- Error: {exc}"]))
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
