from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import configure_stdio


def _load_score(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None


def build_report(
    *,
    candidate: str,
    real_repo_count: int,
    example_app_complete: bool,
    operator_ux_ready: bool,
    shipping_intelligence_tuned: bool,
    strategic_pull_confirmed: bool,
    candidate_score: float | None,
    minimum_score: float,
) -> dict:
    blockers: list[str] = []
    if real_repo_count < 1:
        blockers.append("Lane 1 is not yet proven on a real repo.")
    if not example_app_complete:
        blockers.append("The example app is not complete yet.")
    if not operator_ux_ready:
        blockers.append("Operator UX is not yet clear enough.")
    if not shipping_intelligence_tuned:
        blockers.append("Shipping intelligence has not been tuned from real usage yet.")
    if not strategic_pull_confirmed:
        blockers.append("Candidate lane has not yet shown stronger product pull than further hardening on lane 1.")
    if candidate_score is None:
        blockers.append("No candidate lane score was provided.")
    elif candidate_score < minimum_score:
        blockers.append(f"Candidate score {candidate_score} is below the minimum {minimum_score}.")
    status = "PASS" if not blockers else "FAIL"
    return {
        "status": status,
        "candidate": candidate,
        "real_repo_count": real_repo_count,
        "example_app_complete": example_app_complete,
        "operator_ux_ready": operator_ux_ready,
        "shipping_intelligence_tuned": shipping_intelligence_tuned,
        "strategic_pull_confirmed": strategic_pull_confirmed,
        "candidate_score": candidate_score,
        "minimum_score": minimum_score,
        "blockers": blockers,
        "next_action": f"Open lane 2 for {candidate}." if status == "PASS" else "Continue hardening lane 1 or gather stronger lane-2 evidence.",
    }


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Apply the Forge lane-2 evidence and strategy gate.")
    parser.add_argument("--candidate", required=True, help="Candidate lane id")
    parser.add_argument("--real-repo-count", type=int, default=0, help="Number of real repos with lane-1 evidence")
    parser.add_argument("--example-app-complete", action="store_true", help="Mark the lane-1 example app as complete")
    parser.add_argument("--operator-ux-ready", action="store_true", help="Mark operator UX as ready")
    parser.add_argument("--shipping-intelligence-tuned", action="store_true", help="Mark shipping intelligence as tuned from real use")
    parser.add_argument("--strategic-pull-confirmed", action="store_true", help="Mark that the candidate lane has stronger product pull than more hardening on lane 1")
    parser.add_argument("--candidate-score", type=float, default=None, help="Explicit candidate score")
    parser.add_argument("--score-path", type=Path, default=None, help="Optional path to a lane-score JSON report")
    parser.add_argument("--minimum-score", type=float, default=70.0, help="Minimum score required to open lane 2")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    score_report = _load_score(args.score_path.resolve() if args.score_path else None)
    candidate_score = args.candidate_score if args.candidate_score is not None else (score_report.get("total") if isinstance(score_report, dict) else None)
    report = build_report(
        candidate=args.candidate,
        real_repo_count=args.real_repo_count,
        example_app_complete=args.example_app_complete,
        operator_ux_ready=args.operator_ux_ready,
        shipping_intelligence_tuned=args.shipping_intelligence_tuned,
        strategic_pull_confirmed=args.strategic_pull_confirmed,
        candidate_score=candidate_score,
        minimum_score=args.minimum_score,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
