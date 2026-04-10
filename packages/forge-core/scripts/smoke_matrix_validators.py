from __future__ import annotations

from common import DEFAULT_DELEGATION_PREFERENCE, compat_default_extra, load_preferences_compat, merge_extra_preferences


def _expect_equal(failures: list[str], actual: object, expected: object, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def _expect_contains_in_collection(failures: list[str], values: list[str], expected: str, label: str) -> None:
    if not any(expected in value for value in values):
        failures.append(f"{label} missing substring: {expected!r}")


def validate_route_case(case: dict, report: dict) -> list[str]:
    detected = report["detected"]
    host_supports_subagents = detected.get("host_supports_subagents", False)
    failures: list[str] = []

    _expect_equal(failures, detected["intent"], case["expected_intent"], "intent")
    _expect_equal(failures, detected["complexity"], case["expected_complexity"], "complexity")
    _expect_equal(
        failures,
        detected["verification_profile"],
        case.get("expected_verification_profile"),
        "verification_profile",
    )
    if "expected_session_mode" in case:
        _expect_equal(failures, detected["session_mode"], case["expected_session_mode"], "session_mode")
    if "expected_skills" in case:
        _expect_equal(failures, detected["forge_skills"], case["expected_skills"], "forge_skills")
    if "expected_skill_prefix" in case:
        prefix = case["expected_skill_prefix"]
        _expect_equal(failures, detected["forge_skills"][: len(prefix)], prefix, "forge_skill_prefix")
    if "expected_domain_skills" in case:
        _expect_equal(failures, detected["domain_skills"], case["expected_domain_skills"], "domain_skills")
    if "expected_local_companions" in case:
        _expect_equal(failures, detected["local_companions"], case["expected_local_companions"], "local_companions")
    if "expected_quality_profile" in case:
        _expect_equal(failures, detected["quality_profile"], case["expected_quality_profile"], "quality_profile")
    if "expected_execution_pipeline" in case:
        _expect_equal(
            failures,
            detected["execution_pipeline"],
            case["expected_execution_pipeline"],
            "execution_pipeline",
        )
    if "expected_resolved_delegation_preference" in case:
        _expect_equal(
            failures,
            detected["resolved_delegation_preference"],
            case["expected_resolved_delegation_preference"],
            "resolved_delegation_preference",
        )
    if "expected_effective_delegation_mode" in case:
        _expect_equal(
            failures,
            detected["effective_delegation_mode"],
            case["expected_effective_delegation_mode"],
            "effective_delegation_mode",
        )
    if "expected_delegation_strategy" in case:
        expected_strategy = (
            case["expected_delegation_strategy_when_subagents"]
            if host_supports_subagents and "expected_delegation_strategy_when_subagents" in case
            else case["expected_delegation_strategy"]
        )
        _expect_equal(failures, detected["delegation_strategy"], expected_strategy, "delegation_strategy")
    if "expected_host_skills" in case:
        _expect_equal(failures, detected["host_skills"], case["expected_host_skills"], "host_skills")
    if "expected_host_skills_when_subagents" in case and host_supports_subagents:
        _expect_equal(
            failures,
            detected["host_skills"],
            case["expected_host_skills_when_subagents"],
            "host_skills",
        )
    return failures


def validate_router_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    codes = [item["code"] for item in report["findings"]]
    normalized_router_map = report["router_map"].replace("\\", "/")

    _expect_equal(failures, report["status"], case["expected_status"], "status")
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
    _expect_equal(failures, report["counts"]["warn"], case["expected_warn_count"], "warn_count")
    return failures


def validate_preferences_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(failures, report["source"]["type"], case["expected_source_type"], "source_type")
    _expect_equal(failures, report["preferences"], case["expected_preferences"], "preferences")
    if "expected_extra" in case:
        expected_extra = merge_extra_preferences(
            compat_default_extra(load_preferences_compat()),
            {"delegation_preference": DEFAULT_DELEGATION_PREFERENCE},
        )
        expected_extra = merge_extra_preferences(expected_extra, case["expected_extra"])
        _expect_equal(failures, report.get("extra", {}), expected_extra, "extra")
    for key, expected in case.get("expected_response_style", {}).items():
        _expect_equal(failures, report["response_style"].get(key), expected, f"response_style.{key}")
    for expected in case.get("expected_warning_contains", []):
        _expect_contains_in_collection(failures, report.get("warnings", []), expected, "warning")
    return failures


def validate_help_next_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(failures, report["current_stage"], case["expected_stage"], "current_stage")
    _expect_equal(failures, report["suggested_workflow"], case["expected_workflow"], "suggested_workflow")
    _expect_equal(failures, report["current_focus"], case["expected_focus"], "current_focus")
    _expect_equal(failures, report["recommended_action"], case["expected_recommended_action"], "recommended_action")
    for expected in case.get("expected_warning_contains", []):
        _expect_contains_in_collection(failures, report.get("warnings", []), expected, "warning")
    return failures


def validate_run_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(failures, report["state"], case["expected_state"], "state")
    _expect_equal(failures, report["command_kind"], case["expected_command_kind"], "command_kind")
    _expect_equal(failures, report["suggested_workflow"], case["expected_workflow"], "suggested_workflow")
    if "expected_readiness_detected" in case:
        _expect_equal(
            failures,
            report["readiness_detected"],
            case["expected_readiness_detected"],
            "readiness_detected",
        )
    if "expected_translation_category" in case:
        translation = report.get("error_translation") or {}
        _expect_equal(
            failures,
            translation.get("category"),
            case["expected_translation_category"],
            "error_translation.category",
        )
    return failures


def validate_error_translation_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    translation = report["translation"]

    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(failures, translation["category"], case["expected_category"], "translation.category")
    if case["expected_message_contains"] not in translation["human_message"].lower():
        failures.append(f"human_message missing substring: {case['expected_message_contains']!r}")
    if case["expected_action_contains"] not in translation["suggested_action"].lower():
        failures.append(f"suggested_action missing substring: {case['expected_action_contains']!r}")
    return failures


def validate_bump_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []

    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(failures, report["current_version"], case["expected_current_version"], "current_version")
    _expect_equal(failures, report["target_version"], case["expected_target_version"], "target_version")
    for label in ("selected_bump", "bump_source", "inference_confidence", "inferred_from"):
        expected_key = f"expected_{label}"
        if expected_key in case:
            _expect_equal(failures, report[label], case[expected_key], label)
    if "expected_inferred_from_any" in case and report["inferred_from"] not in case["expected_inferred_from_any"]:
        failures.append(
            "inferred_from: expected one of {expected!r}, got {actual!r}".format(
                expected=case["expected_inferred_from_any"],
                actual=report["inferred_from"],
            )
        )
    return failures
