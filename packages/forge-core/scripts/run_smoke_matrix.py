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
PREFERENCES_CASES = json.loads((FIXTURES_DIR / "preferences_cases.json").read_text(encoding="utf-8"))
HELP_NEXT_CASES = json.loads((FIXTURES_DIR / "help_next_cases.json").read_text(encoding="utf-8"))
RUN_CASES = json.loads((FIXTURES_DIR / "run_cases.json").read_text(encoding="utf-8"))
ERROR_TRANSLATION_CASES = json.loads((FIXTURES_DIR / "error_translation_cases.json").read_text(encoding="utf-8"))
BUMP_CASES = json.loads((FIXTURES_DIR / "bump_cases.json").read_text(encoding="utf-8"))
ROLLBACK_CASES = json.loads((FIXTURES_DIR / "rollback_cases.json").read_text(encoding="utf-8"))
PREFERENCES_WRITE_CASES = json.loads((FIXTURES_DIR / "preferences_write_cases.json").read_text(encoding="utf-8"))
WORKSPACE_INIT_CASES = json.loads((FIXTURES_DIR / "workspace_init_cases.json").read_text(encoding="utf-8"))
RUN_HELPERS_DIR = FIXTURES_DIR / "run_helpers"


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
    host_supports_subagents = detected.get("host_supports_subagents", False)
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
    if "expected_delegation_strategy" in case:
        expected_strategy = case["expected_delegation_strategy_when_subagents"] if host_supports_subagents and "expected_delegation_strategy_when_subagents" in case else case["expected_delegation_strategy"]
        expect(detected["delegation_strategy"], expected_strategy, "delegation_strategy")
    if "expected_host_skills" in case:
        expect(detected["host_skills"], case["expected_host_skills"], "host_skills")
    if host_supports_subagents and "expected_host_skills_when_subagents" in case:
        expect(detected["host_skills"], case["expected_host_skills_when_subagents"], "host_skills")

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


def validate_preferences_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["status"], case["expected_status"], "status")
    expect(report["source"]["type"], case["expected_source_type"], "source_type")
    expect(report["preferences"], case["expected_preferences"], "preferences")

    for key, expected in case.get("expected_response_style", {}).items():
        actual = report["response_style"].get(key)
        expect(actual, expected, f"response_style.{key}")

    warnings = report.get("warnings", [])
    for expected in case.get("expected_warning_contains", []):
        if not any(expected in warning for warning in warnings):
            failures.append(f"warning missing substring: {expected!r}")

    return failures


def validate_help_next_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["status"], case["expected_status"], "status")
    expect(report["current_stage"], case["expected_stage"], "current_stage")
    expect(report["suggested_workflow"], case["expected_workflow"], "suggested_workflow")
    expect(report["current_focus"], case["expected_focus"], "current_focus")
    expect(report["recommended_action"], case["expected_recommended_action"], "recommended_action")

    warnings = report.get("warnings", [])
    for expected in case.get("expected_warning_contains", []):
        if not any(expected in warning for warning in warnings):
            failures.append(f"warning missing substring: {expected!r}")

    return failures


def validate_run_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["status"], case["expected_status"], "status")
    expect(report["state"], case["expected_state"], "state")
    expect(report["command_kind"], case["expected_command_kind"], "command_kind")
    expect(report["suggested_workflow"], case["expected_workflow"], "suggested_workflow")
    if "expected_readiness_detected" in case:
        expect(report["readiness_detected"], case["expected_readiness_detected"], "readiness_detected")
    if "expected_translation_category" in case:
        translation = report.get("error_translation") or {}
        expect(translation.get("category"), case["expected_translation_category"], "error_translation.category")

    return failures


def validate_error_translation_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    translation = report["translation"]
    expect(report["status"], case["expected_status"], "status")
    expect(translation["category"], case["expected_category"], "translation.category")
    if case["expected_message_contains"] not in translation["human_message"].lower():
        failures.append(f"human_message missing substring: {case['expected_message_contains']!r}")
    if case["expected_action_contains"] not in translation["suggested_action"].lower():
        failures.append(f"suggested_action missing substring: {case['expected_action_contains']!r}")
    return failures


def validate_bump_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["status"], case["expected_status"], "status")
    expect(report["current_version"], case["expected_current_version"], "current_version")
    expect(report["target_version"], case["expected_target_version"], "target_version")
    if "expected_selected_bump" in case:
        expect(report["selected_bump"], case["expected_selected_bump"], "selected_bump")
    if "expected_bump_source" in case:
        expect(report["bump_source"], case["expected_bump_source"], "bump_source")
    if "expected_inference_confidence" in case:
        expect(report["inference_confidence"], case["expected_inference_confidence"], "inference_confidence")
    if "expected_inferred_from" in case:
        expect(report["inferred_from"], case["expected_inferred_from"], "inferred_from")
    if "expected_inferred_from_any" in case and report["inferred_from"] not in case["expected_inferred_from_any"]:
        failures.append(
            "inferred_from: expected one of {expected!r}, got {actual!r}".format(
                expected=case["expected_inferred_from_any"],
                actual=report["inferred_from"],
            )
        )
    return failures


def validate_rollback_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["status"], case["expected_status"], "status")
    expect(report["recommended_strategy"], case["expected_strategy"], "recommended_strategy")
    expect(report["suggested_workflow"], case["expected_workflow"], "suggested_workflow")
    for expected in case.get("expected_warning_contains", []):
        if not any(expected in warning for warning in report.get("warnings", [])):
            failures.append(f"warning missing substring: {expected!r}")
    return failures


def validate_preferences_write_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["status"], case["expected_status"], "status")
    expect(report["preferences"], case["expected_preferences"], "preferences")
    expect(report["changed_fields"], case["expected_changed_fields"], "changed_fields")
    return failures


def validate_workspace_init_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    def expect(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    expect(report["workspace_mode"], case["expected_mode"], "workspace_mode")
    expect(report["recommended_next_workflow"], case["expected_next_workflow"], "recommended_next_workflow")
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


def run_preferences_suite() -> list[dict]:
    preferences_script = ROOT_DIR / "scripts" / "resolve_preferences.py"
    results: list[dict] = []
    for case in PREFERENCES_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [sys.executable, str(preferences_script), "--workspace", str(workspace), "--format", "json"]
        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "preferences",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_preferences_case(case, report)
        results.append(
            {
                "suite": "preferences",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_help_next_suite() -> list[dict]:
    navigator_script = ROOT_DIR / "scripts" / "resolve_help_next.py"
    results: list[dict] = []
    for case in HELP_NEXT_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [
            sys.executable,
            str(navigator_script),
            "--workspace",
            str(workspace),
            "--mode",
            case["mode"],
            "--format",
            "json",
        ]
        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "help-next",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_help_next_case(case, report)
        results.append(
            {
                "suite": "help-next",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def resolve_run_command(parts: list[str]) -> list[str]:
    resolved: list[str] = []
    for part in parts:
        candidate = RUN_HELPERS_DIR / part
        if part.endswith(".py") and candidate.exists():
            resolved.append(str(candidate))
        else:
            resolved.append(part)
    return resolved


def run_run_suite() -> list[dict]:
    run_script = ROOT_DIR / "scripts" / "run_with_guidance.py"
    results: list[dict] = []
    for case in RUN_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [
            sys.executable,
            str(run_script),
            "--workspace",
            str(workspace),
            "--timeout-ms",
            str(case["timeout_ms"]),
            "--format",
            "json",
            "--",
            *resolve_run_command(case["command"]),
        ]
        completed = run_command(command)
        if completed.returncode not in {0, 1}:
            results.append(
                {
                    "suite": "run",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"unexpected exit code {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_run_case(case, report)
        results.append(
            {
                "suite": "run",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_error_translation_suite() -> list[dict]:
    translate_script = ROOT_DIR / "scripts" / "translate_error.py"
    results: list[dict] = []
    for case in ERROR_TRANSLATION_CASES:
        command = [
            sys.executable,
            str(translate_script),
            "--error-text",
            case["error_text"],
            "--format",
            "json",
        ]
        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "error-translation",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_error_translation_case(case, report)
        results.append(
            {
                "suite": "error-translation",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_bump_suite() -> list[dict]:
    bump_script = ROOT_DIR / "scripts" / "prepare_bump.py"
    results: list[dict] = []
    for case in BUMP_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [
            sys.executable,
            str(bump_script),
            "--workspace",
            str(workspace),
            "--bump",
            case["bump"],
            "--format",
            "json",
        ]
        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "bump",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_bump_case(case, report)
        results.append(
            {
                "suite": "bump",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_rollback_suite() -> list[dict]:
    rollback_script = ROOT_DIR / "scripts" / "resolve_rollback.py"
    results: list[dict] = []
    for case in ROLLBACK_CASES:
        command = [
            sys.executable,
            str(rollback_script),
            "--scope",
            case["scope"],
            "--customer-impact",
            case["customer_impact"],
            "--data-risk",
            case["data_risk"],
            "--format",
            "json",
        ]
        if case["has_rollback_artifact"]:
            command.append("--has-rollback-artifact")

        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "rollback",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_rollback_case(case, report)
        results.append(
            {
                "suite": "rollback",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_preferences_write_suite() -> list[dict]:
    write_script = ROOT_DIR / "scripts" / "write_preferences.py"
    results: list[dict] = []
    for case in PREFERENCES_WRITE_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [
            sys.executable,
            str(write_script),
            "--workspace",
            str(workspace),
            "--format",
            "json",
            *case["args"],
        ]
        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "preferences-write",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_preferences_write_case(case, report)
        results.append(
            {
                "suite": "preferences-write",
                "name": case["name"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
        )
    return results


def run_workspace_init_suite() -> list[dict]:
    init_script = ROOT_DIR / "scripts" / "initialize_workspace.py"
    results: list[dict] = []
    for case in WORKSPACE_INIT_CASES:
        workspace = WORKSPACES_DIR / case["workspace_fixture"]
        command = [
            sys.executable,
            str(init_script),
            "--workspace",
            str(workspace),
            "--format",
            "json",
            *case["args"],
        ]
        completed = run_command(command)
        if completed.returncode != 0:
            results.append(
                {
                    "suite": "workspace-init",
                    "name": case["name"],
                    "status": "FAIL",
                    "failures": [f"command exited {completed.returncode}", completed.stderr.strip() or completed.stdout.strip()],
                }
            )
            continue

        report = json.loads(completed.stdout)
        failures = validate_workspace_init_case(case, report)
        results.append(
            {
                "suite": "workspace-init",
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
        choices=[
            "route-preview",
            "router-check",
            "preferences",
            "help-next",
            "run",
            "error-translation",
            "bump",
            "rollback",
            "preferences-write",
            "workspace-init",
            "all",
        ],
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
    if args.suite in {"preferences", "all"}:
        results.extend(run_preferences_suite())
    if args.suite in {"help-next", "all"}:
        results.extend(run_help_next_suite())
    if args.suite in {"run", "all"}:
        results.extend(run_run_suite())
    if args.suite in {"error-translation", "all"}:
        results.extend(run_error_translation_suite())
    if args.suite in {"bump", "all"}:
        results.extend(run_bump_suite())
    if args.suite in {"rollback", "all"}:
        results.extend(run_rollback_suite())
    if args.suite in {"preferences-write", "all"}:
        results.extend(run_preferences_write_suite())
    if args.suite in {"workspace-init", "all"}:
        results.extend(run_workspace_init_suite())

    summary = summarize(results)
    payload = {"summary": summary, "results": results}
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(format_text(summary, results))

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
