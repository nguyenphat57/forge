from __future__ import annotations

from pathlib import Path

from companion_invoke import invoke_companion_capability


def _feature_list(match: dict) -> list[str]:
    return sorted(key for key, matched in match.get("features", {}).items() if matched)


def build_operator_context(match: dict, workspace: Path) -> dict:
    report = invoke_companion_capability(match, "command_profiles", workspace)
    profile = report.get("profile") if isinstance(report, dict) else None
    verification_pack = report.get("verification_pack") if isinstance(report, dict) else None
    pack_id = verification_pack.get("id") if isinstance(verification_pack, dict) else None
    pack_steps = verification_pack.get("steps") if isinstance(verification_pack, dict) else []
    return {
        "id": match["id"],
        "package": match["package"],
        "strength": match["strength"],
        "features": _feature_list(match),
        "profile": profile,
        "package_manager": report.get("package_manager") if isinstance(report, dict) else None,
        "commands": report.get("commands") if isinstance(report, dict) else {},
        "verification_pack": pack_id,
        "verification_steps": pack_steps if isinstance(pack_steps, list) else [],
    }


def collect_operator_context(matches: list[dict], workspace: Path) -> list[dict]:
    return [build_operator_context(match, workspace) for match in matches]
