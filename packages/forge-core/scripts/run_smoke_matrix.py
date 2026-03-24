from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
WORKSPACES_DIR = FIXTURES_DIR / "workspaces"
ROUTE_CASES = json.loads((FIXTURES_DIR / "route_preview_cases.json").read_text(encoding="utf-8"))
ROUTER_CASES = json.loads((FIXTURES_DIR / "router_check_cases.json").read_text(encoding="utf-8"))


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def validate_route_case(case: dict, report: dict) -> list[str]:
    detected = report["detected"]
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(detected["intent"], case["expected_intent"], "intent")
    expect(detected["complexity"], case["expected_complexity"], "complexity")
    expect(detected["verification_profile"], case.get("expected_verification_profile"), "verification_profile")

    if "expected_skills" in case:
        expect(detected["forge_skills"], case["expected_skills"], "forge_skills")
    if "expected_skill_prefix" in case:
        prefix = case["expected_skill_prefix"]
        expect(detected["forge_skills"][: len(prefix)], prefix, "forge_skill_prefix")
    if "expected_domain_skills" in case:
        expect(detected["domain_skills"], case["expected_domain_skills"], "domain_skills")
    if "expected_local_companions" in case:
        expect(detected["local_companions"], case["expected_local_companions"], "local_companions")
    if "expected_quality_profile" in case:
        expect(detected["quality_profile"], case["expected_quality_profile"], "quality_profile")
    if "expected_execution_pipeline" in case:
        expect(detected["execution_pipeline"], case["expected_execution_pipeline"], "execution_pipeline")

    return failures


def validate_router_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    codes = [item["code"] for item in report["findings"]]
    normalized_router_map = report["router_map"].replace("\\", "/")

    if report["status"] != case["expected_status"]:
        failures.append(f"status: expected {case['expected_status']!r}, got {report['status']!r}")
    if not normalized_router_map.endswith(case["expected_router_suffix"]):
        failures.append(
            "router_map: expected suffix {expected!r}, got {actual!r}".format(
                expected=case["expected_router_suffix"],
                actual=report["router_map"],
            )
        )
    for code in case.get("expected_codes", []):
        if code not in codes:
            failures.append(f"missing finding code: {code}")
    if report["counts"]["warn"] != case["expected_warn_count"]:
        failures.append(
            "warn_count: expected {expected!r}, got {actual!r}".format(
                expected=case["expected_warn_count"],
                actual=report["counts"]["warn"],
            )
        )
    return failures


def run_route_suite() -> list[dict]:
    route_script = ROOT_DIR / "scripts" / "route_preview.py"
    results: list[dict] = []
    for case in ROUTE_CASES:
        command = [sys.executable, str(route_script), case["prompt"], "--format", "json"]
        for signal in case.get("repo_signals", []):
            command.extend(["--repo-signal", signal])
        if case.get("workspace_fixture") and case.get("workspace_router"):
            router_path = WORKSPACES_DIR / case["workspace_fixture"] / case["workspace_router"]
            command.extend(["--workspace-router", str(router_path)])

        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "route-preview",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_route_case(case, report)
        results.append(
            {
                "suite": "route-preview",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_router_suite() -> list[dict]:
    router_script = ROOT_DIR / "scripts" / "check_workspace_router.py"
    results: list[dict] = []
    for case in ROUTER_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [sys.executable, str(router_script), str(workspace), "--format", "json"]
        completed = run_command(command)
        if completed.returncode not in {0, 1}:
            results.append(
                {
                    "suite": "router-check",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"unexpected exit code {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_router_case(case, report)
        results.append(
            {
                "suite": "router-check",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def summarize(results: list[dict]) -> dict:
    passes = sum(1 for item in results if item["status"] == "PASS")
    failures = [item for item in results if item["status"] == "FAIL"]
    return {
        "total": len(results),
        "passed": passes,
        "failed": len(failures),
        "failures": failures,
    }


def format_text(summary: dict, results: list[dict]) -> str:
    lines = [
        "Forge Smoke Matrix",
        f"- Total: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "- Results:",
    ]
    for item in results:
        lines.append(f"  - [{item['status']}] {item['suite']} :: {item['name']}")
        for failure in item["failures"]:
            lines.append(f"    - {failure}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Forge smoke matrices for route preview and router checks.")
    parser.add_argument(
        "--suite",
        choices=["route-preview", "router-check", "all"],
        default="all",
        help="Smoke suite to run",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    results: list[dict] = []
    if args.suite in {"route-preview", "all"}:
        results.extend(run_route_suite())
    if args.suite in {"router-check", "all"}:
        results.extend(run_router_suite())

    summary = summarize(results)
    payload = {"summary": summary, "results": results}
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(summary, results))

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
