from __future__ import annotations

from _forge_core_command import bootstrap_shared_paths

bootstrap_shared_paths()

import argparse
import json
from pathlib import Path

from common import configure_stdio
from prepare_bump_git import (
    BREAKING_TEXT_HINTS,
    CAPABILITY_PATH_HINTS,
    DOC_PATH_HINTS,
    PUBLIC_SURFACE_PATH_HINTS,
    RELEASE_ARTIFACTS,
    TEST_PATH_HINTS,
    collect_release_diff,
    dedupe_entries,
    infer_bump_token,
    infer_confidence,
    is_doc_or_test_path,
    is_git_workspace,
    is_release_artifact,
    normalize_repo_path,
    parse_name_status,
    parse_status_porcelain,
    path_matches_hints,
    resolve_release_base_commit,
    run_git_command,
)
from prepare_bump_report import build_report, format_text
from prepare_bump_semver import SEMVER_PATTERN, bump_version, detect_verify_command, format_version, parse_version, update_changelog_content


EXPLICIT_BUMP_TOKENS = {"patch", "minor", "major"}


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
