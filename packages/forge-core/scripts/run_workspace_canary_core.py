from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import check_workspace_router
import route_preview
from common import detect_runtimes, load_registry


MARKER_FILES = (
    "AGENTS.md",
    "package.json",
    "tsconfig.json",
    "tsconfig.app.json",
    "vite.config.ts",
    "vite.config.js",
    "pyproject.toml",
    "requirements.txt",
    "pytest.ini",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "wrangler.toml",
    "wrangler.jsonc",
    "capacitor.config.ts",
)

MARKER_DIRS = (
    ".agent",
    "src",
    "tests",
    "android",
    "ios",
    "supabase",
    "api",
)


def collect_repo_signals(workspace: Path) -> list[str]:
    signals: list[str] = []
    for marker in MARKER_FILES:
        if (workspace / marker).exists():
            signals.append(marker)
    for marker in MARKER_DIRS:
        if (workspace / marker).exists():
            signals.append(marker)
    return signals


def build_route_args(prompt: str, repo_signals: list[str], workspace_router: Path | None) -> Namespace:
    return Namespace(
        prompt=prompt,
        repo_signal=repo_signals,
        workspace_router=workspace_router,
        changed_files=None,
        has_harness="auto",
        format="json",
        persist=False,
        output_dir=None,
    )


def default_scenarios(runtimes: list[str], can_check_local_companions: bool) -> list[dict]:
    build_prompt = "Implement tested API endpoint" if "python" in runtimes else "Implement a tested feature with clear verification"
    debug_prompt = (
        "Debug failing pytest flow after parser refactor"
        if "python" in runtimes
        else "Fix regression where the app crashes after a recent change"
    )
    scenarios = [
        {
            "name": "review",
            "prompt": "Review code before merge",
            "expected_intent": "REVIEW",
            "verification": "absent",
            "max_local_companions": 0,
            "expected_quality_profile": "standard",
        },
        {
            "name": "session",
            "prompt": "Continue the task in progress",
            "expected_intent": "SESSION",
            "verification": "absent",
            "max_local_companions": 0,
            "expected_quality_profile": "standard",
        },
        {
            "name": "build",
            "prompt": build_prompt,
            "expected_intent": "BUILD",
            "verification": "present",
        },
        {
            "name": "debug",
            "prompt": debug_prompt,
            "expected_intent": "DEBUG",
            "verification": "present",
        },
        {
            "name": "deploy",
            "prompt": "Deploy the app to production",
            "expected_intent": "DEPLOY",
            "verification": "absent",
        },
    ]
    if can_check_local_companions:
        scenarios.append(
            {
                "name": "local-companion",
                "prompt": "Implement endpoint" if "python" in runtimes else build_prompt,
                "expected_intent": "BUILD",
                "verification": "present",
                "require_local_companion": True,
            }
        )
    return scenarios


def evaluate_route_scenario(
    scenario: dict,
    repo_signals: list[str],
    workspace_router: Path | None,
) -> dict:
    preview = route_preview.build_report(build_route_args(scenario["prompt"], repo_signals, workspace_router))
    detected = preview["detected"]
    failures: list[str] = []

    if detected["intent"] != scenario["expected_intent"]:
        failures.append(
            "Expected intent {expected}, got {actual}.".format(
                expected=scenario["expected_intent"],
                actual=detected["intent"],
            )
        )

    verification_profile = detected["verification_profile"]
    if scenario["verification"] == "present" and verification_profile is None:
        failures.append("Expected a verification profile but none was selected.")
    if scenario["verification"] == "absent" and verification_profile is not None:
        failures.append(f"Expected no verification profile but got {verification_profile}.")
    if "expected_quality_profile" in scenario and detected["quality_profile"] != scenario["expected_quality_profile"]:
        failures.append(
            "Expected quality profile {expected}, got {actual}.".format(
                expected=scenario["expected_quality_profile"],
                actual=detected["quality_profile"],
            )
        )
    if len(detected["local_companions"]) > scenario.get("max_local_companions", len(detected["local_companions"])):
        failures.append(
            "Expected at most {expected} local companion(s), got {actual}.".format(
                expected=scenario["max_local_companions"],
                actual=len(detected["local_companions"]),
            )
        )

    if scenario.get("require_local_companion") and not detected["local_companions"]:
        failures.append("Expected at least one local companion from runtime signals, but none were selected.")

    return {
        "name": scenario["name"],
        "prompt": scenario["prompt"],
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "detected": detected,
        "activation_line": preview["activation_line"],
    }


def run_router_check(workspace: Path) -> dict | None:
    agents_path = workspace / "AGENTS.md"
    if not agents_path.exists():
        return None
    args = Namespace(
        workspace=workspace,
        agents=None,
        router_map=None,
        format="json",
        persist=False,
        output_dir=None,
    )
    return check_workspace_router.check_workspace(args)


def build_report(workspace: Path, workspace_name: str | None = None) -> dict:
    registry = load_registry()
    repo_signals = collect_repo_signals(workspace)
    agents_path = workspace / "AGENTS.md"
    workspace_router = route_preview.resolve_workspace_router(agents_path if agents_path.exists() else None)
    runtimes = detect_runtimes(repo_signals, registry)
    has_local_skills = (workspace / ".agent" / "skills").exists()
    scenarios = default_scenarios(
        runtimes,
        can_check_local_companions=workspace_router is not None and has_local_skills and bool(runtimes),
    )
    scenario_reports = [evaluate_route_scenario(scenario, repo_signals, workspace_router) for scenario in scenarios]
    router_report = run_router_check(workspace)

    blockers = [
        "{name}: {message}".format(name=scenario["name"], message=message)
        for scenario in scenario_reports
        for message in scenario["failures"]
    ]
    warnings: list[str] = []
    if router_report is not None:
        if router_report["status"] == "FAIL":
            blockers.append("router-check: workspace router validation failed.")
        elif router_report["status"] == "WARN":
            warnings.extend(
                "router-check: {message}".format(message=item["message"])
                for item in router_report["findings"]
                if item["level"] == "warn"
            )

    status = "fail" if blockers else ("warn" if warnings else "pass")
    summary = (
        "Core routing pack passed on {workspace} ({passed}/{total} scenarios).".format(
            workspace=workspace_name or workspace.name,
            passed=sum(1 for item in scenario_reports if item["status"] == "PASS"),
            total=len(scenario_reports),
        )
        if status == "pass"
        else "Workspace canary found blockers." if status == "fail" else "Workspace canary passed with warnings."
    )
    return {
        "workspace": str(workspace),
        "workspace_name": workspace_name or workspace.name,
        "workspace_router": str(workspace_router) if workspace_router else None,
        "repo_signals": repo_signals,
        "runtimes": runtimes,
        "status": status,
        "summary": summary,
        "scenarios": scenario_reports,
        "router_check": router_report,
        "warnings": warnings,
        "blockers": blockers,
    }
