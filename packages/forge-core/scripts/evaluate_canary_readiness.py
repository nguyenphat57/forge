from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from common import configure_stdio


PROFILE_RULES = {
    "controlled-rollout": {
        "min_workspaces": 2,
        "min_total_runs": 2,
        "min_observation_days": 1,
        "max_fail_runs": 0,
        "max_warn_workspaces": 1,
        "allow_blockers": False,
    },
    "broad": {
        "min_workspaces": 3,
        "min_total_runs": 6,
        "min_observation_days": 2,
        "max_fail_runs": 0,
        "max_warn_workspaces": 0,
        "allow_blockers": False,
    },
}


def load_runs(root: Path) -> list[dict]:
    runs: list[dict] = []
    if not root.exists():
        return runs
    for path in sorted(root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and {"workspace", "status", "observed_at"} <= payload.keys():
            payload["_path"] = str(path)
            runs.append(payload)
    return runs


def evaluate_runs(runs: list[dict], profile: str) -> dict:
    rules = PROFILE_RULES[profile]
    by_workspace: dict[str, list[dict]] = defaultdict(list)
    for run in runs:
        by_workspace[run["workspace"]].append(run)

    latest_runs: dict[str, dict] = {}
    for workspace, items in by_workspace.items():
        latest_runs[workspace] = sorted(items, key=lambda item: item["observed_at"])[-1]

    fail_runs = [run for run in runs if run["status"] == "fail"]
    warn_workspaces = [workspace for workspace, run in latest_runs.items() if run["status"] == "warn"]
    observation_days = sorted({run["observed_at"][:10] for run in runs if len(run["observed_at"]) >= 10})
    blocking_workspaces = [
        workspace
        for workspace, run in latest_runs.items()
        if run.get("blockers")
    ]

    failures: list[str] = []
    if len(latest_runs) < rules["min_workspaces"]:
        failures.append(
            f"Need at least {rules['min_workspaces']} workspaces, found {len(latest_runs)}."
        )
    if len(runs) < rules["min_total_runs"]:
        failures.append(
            f"Need at least {rules['min_total_runs']} total canary runs, found {len(runs)}."
        )
    if len(observation_days) < rules["min_observation_days"]:
        failures.append(
            f"Need at least {rules['min_observation_days']} observation day(s), found {len(observation_days)}."
        )
    if len(fail_runs) > rules["max_fail_runs"]:
        failures.append(
            f"Fail runs exceed limit: {len(fail_runs)} > {rules['max_fail_runs']}."
        )
    if len(warn_workspaces) > rules["max_warn_workspaces"]:
        failures.append(
            f"Warn workspaces exceed limit: {len(warn_workspaces)} > {rules['max_warn_workspaces']}."
        )
    if not rules["allow_blockers"] and blocking_workspaces:
        failures.append(
            "Latest canary runs still contain blockers for: {workspaces}.".format(
                workspaces=", ".join(sorted(blocking_workspaces))
            )
        )

    return {
        "profile": profile,
        "rules": rules,
        "status": "PASS" if not failures else "FAIL",
        "summary": {
            "workspaces": len(latest_runs),
            "total_runs": len(runs),
            "observation_days": len(observation_days),
            "fail_runs": len(fail_runs),
            "warn_workspaces": len(warn_workspaces),
            "blocking_workspaces": sorted(blocking_workspaces),
        },
        "latest_runs": {
            workspace: {
                "status": run["status"],
                "observed_at": run["observed_at"],
                "summary": run["summary"],
                "path": run["_path"],
            }
            for workspace, run in sorted(latest_runs.items())
        },
        "failures": failures,
    }


def format_text(report: dict) -> str:
    lines = [
        "Forge Canary Readiness",
        f"- Profile: {report['profile']}",
        f"- Status: {report['status']}",
        f"- Workspaces: {report['summary']['workspaces']}",
        f"- Total runs: {report['summary']['total_runs']}",
        f"- Observation days: {report['summary']['observation_days']}",
        f"- Fail runs: {report['summary']['fail_runs']}",
        f"- Warn workspaces: {report['summary']['warn_workspaces']}",
        f"- Blocking workspaces: {', '.join(report['summary']['blocking_workspaces']) or '(none)'}",
        "- Latest workspace runs:",
    ]
    for workspace, run in report["latest_runs"].items():
        lines.append(f"  - {workspace}: [{run['status']}] {run['summary']} ({run['observed_at']})")
    if report["failures"]:
        lines.append("- Failures:")
        for item in report["failures"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Failures: (none)")
    return "\n".join(lines)


def main() -> int:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Evaluate Forge canary data against rollout-readiness thresholds.")
    parser.add_argument(
        "path",
        nargs="?",
        default=Path.cwd() / ".forge-artifacts" / "canary-runs",
        type=Path,
        help="Directory containing canary run artifacts",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_RULES.keys()),
        default="controlled-rollout",
        help="Readiness threshold profile",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    runs = load_runs(args.path.resolve())
    report = evaluate_runs(runs, args.profile)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
