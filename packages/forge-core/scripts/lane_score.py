from __future__ import annotations

import argparse
import json

from common import configure_stdio


WEIGHTS = {
    "real_repo_demand": 0.30,
    "core_overlap": 0.25,
    "companion_feasibility": 0.20,
    "shipping_leverage": 0.15,
    "maintenance_cost": 0.10,
}


def _bounded(value: int) -> int:
    return max(0, min(5, value))


def build_report(candidate: str, scores: dict[str, int], notes: list[str]) -> dict:
    normalized = {key: _bounded(int(scores.get(key, 0))) for key in WEIGHTS}
    weighted = {
        "real_repo_demand": normalized["real_repo_demand"] * WEIGHTS["real_repo_demand"],
        "core_overlap": normalized["core_overlap"] * WEIGHTS["core_overlap"],
        "companion_feasibility": normalized["companion_feasibility"] * WEIGHTS["companion_feasibility"],
        "shipping_leverage": normalized["shipping_leverage"] * WEIGHTS["shipping_leverage"],
        "maintenance_cost": (5 - normalized["maintenance_cost"]) * WEIGHTS["maintenance_cost"],
    }
    total = round(sum(weighted.values()) / 5 * 100, 1)
    return {
        "status": "PASS",
        "candidate": candidate,
        "scores": normalized,
        "weighted": weighted,
        "total": total,
        "recommendation": "strong" if total >= 75 else "consider" if total >= 60 else "defer",
        "notes": notes,
    }


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Score a candidate Forge lane using the current lane-expansion rubric.")
    parser.add_argument("--candidate", required=True, help="Candidate lane id")
    parser.add_argument("--real-repo-demand", type=int, default=0, help="0-5 score for how many real repos need this lane")
    parser.add_argument("--core-overlap", type=int, default=0, help="0-5 score for overlap with current core surfaces")
    parser.add_argument("--companion-feasibility", type=int, default=0, help="0-5 score for how feasible a companion is")
    parser.add_argument("--shipping-leverage", type=int, default=0, help="0-5 score for shipping leverage if the lane exists")
    parser.add_argument("--maintenance-cost", type=int, default=0, help="0-5 cost score where higher means more maintenance")
    parser.add_argument("--note", action="append", default=[], help="Repeatable note for the decision memo")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    report = build_report(
        args.candidate,
        {
            "real_repo_demand": args.real_repo_demand,
            "core_overlap": args.core_overlap,
            "companion_feasibility": args.companion_feasibility,
            "shipping_leverage": args.shipping_leverage,
            "maintenance_cost": args.maintenance_cost,
        },
        args.note,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
