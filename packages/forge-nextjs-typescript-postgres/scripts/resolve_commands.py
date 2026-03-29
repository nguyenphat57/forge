from __future__ import annotations

import argparse
import json
from pathlib import Path

from companion_common import detected_features, load_command_profiles, load_package_json, load_verification_packs, package_manager


def _select_profile(features: set[str]) -> dict:
    for profile in load_command_profiles():
        required = profile.get("match_all_features")
        if isinstance(required, list) and set(required).issubset(features):
            return profile
    return {}


def _select_pack(profile_id: str) -> dict:
    for pack in load_verification_packs():
        if pack.get("profile") == profile_id:
            return pack
    return {}


def build_report(workspace: Path) -> dict:
    features = detected_features(workspace)
    selected = _select_profile(features)
    scripts = load_package_json(workspace).get("scripts", {})
    manager = package_manager(workspace)
    commands: dict[str, str] = {}
    for key, fallback in (selected.get("commands") or {}).items():
        script_name = fallback.split()[-1]
        commands[key] = f"{manager} run {script_name}" if isinstance(scripts, dict) and script_name in scripts else f"{manager} {fallback}"
    pack = _select_pack(str(selected.get("id") or ""))
    return {
        "status": "PASS" if selected else "WARN",
        "workspace": str(workspace),
        "profile": selected.get("id"),
        "package_manager": manager,
        "features": sorted(features),
        "commands": commands,
        "verification_pack": pack,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve commands for the Next.js TypeScript Postgres companion.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    report = build_report(args.workspace.resolve())
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
