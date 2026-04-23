from __future__ import annotations

def _expect_equal(failures: list[str], actual: object, expected: object, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def _expect_contains_in_collection(failures: list[str], values: list[str], expected: str, label: str) -> None:
    if not any(expected in value for value in values):
        failures.append(f"{label} missing substring: {expected!r}")


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
    for key, expected in case.get("expected_response_style", {}).items():
        _expect_equal(failures, report["response_style"].get(key), expected, f"response_style.{key}")
    for expected in case.get("expected_warning_contains", []):
        _expect_contains_in_collection(failures, report.get("warnings", []), expected, "warning")
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
