from __future__ import annotations

import json
import sys
from pathlib import Path

from _forge_core_script_proxy import run_forge_core_script


ROOT_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT_DIR / "packages" / "forge-core" / "data" / "orchestrator-registry.json"
ACTION_DISPATCH = {
    "help": ("resolve_help_next.py", ("--mode", "help")),
    "next": ("resolve_help_next.py", ("--mode", "next")),
    "run": ("run_with_guidance.py", ()),
    "bump": ("prepare_bump.py", ()),
}
SESSION_OWNER_ACTIONS = {"resume", "save", "handover"}


def _usage() -> str:
    actions = ", ".join(_valid_actions())
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
            "  python commands/resolve_preferences.py --workspace <workspace> --format json",
            "  python commands/write_preferences.py --workspace <workspace> --detail-level concise --apply",
        ]
    )


def _valid_actions() -> tuple[str, ...]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    surface = payload.get("repo_operator_surface", {})
    actions = surface.get("actions", {}) if isinstance(surface, dict) else {}
    if not isinstance(actions, dict) or not actions:
        raise SystemExit(f"Missing repo_operator_surface.actions in {REGISTRY_PATH}")
    return tuple(actions)


def _normalize_bump_args(args: list[str]) -> list[str]:
    if not args:
        return args
    first = args[0]
    if first.startswith("-"):
        return args
    return ["--bump", first, *args[1:]]


def _dispatch(action: str, args: list[str]) -> tuple[str, list[str]]:
    if action == "bump":
        return "prepare_bump.py", _normalize_bump_args(args)
    if action in ACTION_DISPATCH:
        script_name, prefix = ACTION_DISPATCH[action]
        return script_name, [*prefix, *args]
    raise ValueError(f"Unsupported repo operator action: {action}")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(_usage())
        return 0

    action = sys.argv[1].strip()
    valid_actions = _valid_actions()
    if action not in valid_actions:
        print(_usage(), file=sys.stderr)
        print(f"\nUnsupported action: {action}", file=sys.stderr)
        if action in SESSION_OWNER_ACTIONS:
            print("Session continuity is owned by forge-session-management.", file=sys.stderr)
        return 2

    script_name, forwarded_args = _dispatch(action, sys.argv[2:])
    run_forge_core_script(script_name, argv=forwarded_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
