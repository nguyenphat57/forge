from __future__ import annotations

import sys

from _forge_core_script_proxy import run_forge_core_script


VALID_ACTIONS = (
    "resume",
    "save",
    "handover",
    "help",
    "next",
    "run",
    "bump",
    "rollback",
    "customize",
    "init",
)

WRITE_PREFERENCE_FLAGS = {
    "--scope",
    "--technical-level",
    "--detail-level",
    "--autonomy-level",
    "--pace",
    "--feedback-style",
    "--personality",
    "--language",
    "--orthography",
    "--tone-detail",
    "--output-quality",
    "--custom-rule",
    "--delegation-preference",
    "--clear-field",
    "--clear-language",
    "--clear-orthography",
    "--clear-delegation-preference",
    "--replace",
    "--apply",
}


def _usage() -> str:
    actions = ", ".join(VALID_ACTIONS)
    return "\n".join(
        [
            "Forge Repo Operator",
            "",
            "Usage:",
            "  python scripts/repo_operator.py <action> [args...]",
            "",
            f"Actions: {actions}",
            "",
            "Examples:",
            "  python scripts/repo_operator.py help --workspace <workspace> --format json",
            "  python scripts/repo_operator.py next --workspace <workspace> --format json",
            "  python scripts/repo_operator.py run --workspace <workspace> --timeout-ms 20000 -- <command>",
            "  python scripts/repo_operator.py customize --workspace <workspace> --format json",
            "  python scripts/repo_operator.py customize --workspace <workspace> --detail-level concise --apply",
        ]
    )


def _normalize_bump_args(args: list[str]) -> list[str]:
    if not args:
        return args
    first = args[0]
    if first.startswith("-"):
        return args
    return ["--bump", first, *args[1:]]


def _strip_workspace_arg(args: list[str]) -> list[str]:
    normalized: list[str] = []
    skip_next = False
    for index, item in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if item == "--workspace":
            if index + 1 < len(args):
                skip_next = True
            continue
        normalized.append(item)
    return normalized


def _customize_script_and_args(args: list[str]) -> tuple[str, list[str]]:
    if any(flag in WRITE_PREFERENCE_FLAGS for flag in args):
        return "write_preferences.py", args
    return "resolve_preferences.py", args


def _dispatch(action: str, args: list[str]) -> tuple[str, list[str]]:
    if action == "resume":
        return "session_context.py", ["resume", *args]
    if action == "save":
        return "session_context.py", ["save", *args]
    if action == "handover":
        return "session_context.py", ["save", "--write-handover", *args]
    if action == "help":
        return "resolve_help_next.py", ["--mode", "help", *args]
    if action == "next":
        return "resolve_help_next.py", ["--mode", "next", *args]
    if action == "run":
        return "run_with_guidance.py", args
    if action == "bump":
        return "prepare_bump.py", _normalize_bump_args(args)
    if action == "rollback":
        return "resolve_rollback.py", _strip_workspace_arg(args)
    if action == "customize":
        return _customize_script_and_args(args)
    if action == "init":
        return "initialize_workspace.py", args
    raise ValueError(f"Unsupported repo operator action: {action}")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(_usage())
        return 0

    action = sys.argv[1].strip()
    if action not in VALID_ACTIONS:
        print(_usage(), file=sys.stderr)
        print(f"\nUnsupported action: {action}", file=sys.stderr)
        return 2

    script_name, forwarded_args = _dispatch(action, sys.argv[2:])
    run_forge_core_script(script_name, argv=forwarded_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
