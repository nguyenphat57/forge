from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_ROUTE_FIXTURE_PATH = ROOT_DIR / "packages" / "forge-core" / "tests" / "fixtures" / "route_preview_cases.json"

NORMALIZATION_RULES = {
    "forge-antigravity": {
        "drop_keys": ("expected_host_skills", "expected_host_skills_when_subagents"),
    },
}


def load_core_route_preview_cases() -> list[dict]:
    payload = json.loads(CORE_ROUTE_FIXTURE_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else []


def route_preview_cases_for_bundle(bundle_name: str) -> list[dict] | None:
    rules = NORMALIZATION_RULES.get(bundle_name)
    if rules is None:
        return None
    normalized_cases: list[dict] = []
    for case in load_core_route_preview_cases():
        normalized_case = dict(case)
        for key in rules.get("drop_keys", ()):
            normalized_case.pop(key, None)
        normalized_cases.append(normalized_case)
    return normalized_cases


def materialize_overlay_route_fixtures(bundle_name: str, destination: Path) -> list[Path]:
    route_cases = route_preview_cases_for_bundle(bundle_name)
    if route_cases is None:
        return []
    output_path = destination / "tests" / "fixtures" / "route_preview_cases.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(route_cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return [output_path]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate adapter-specific route preview fixture overlays from core fixtures.")
    parser.add_argument("bundle", choices=sorted(NORMALIZATION_RULES), help="Bundle name")
    parser.add_argument("--output", type=Path, required=True, help="Output bundle root or explicit JSON path")
    args = parser.parse_args()

    output = args.output.resolve()
    if output.suffix.lower() == ".json":
        cases = route_preview_cases_for_bundle(args.bundle)
        if cases is None:
            raise ValueError(f"No route fixture normalization rules for {args.bundle}.")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0

    materialize_overlay_route_fixtures(args.bundle, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
