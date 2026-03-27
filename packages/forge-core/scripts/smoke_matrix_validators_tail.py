from __future__ import annotations


def _expect_equal(failures: list[str], actual: object, expected: object, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def _expect_contains_in_collection(failures: list[str], values: list[str], expected: str, label: str) -> None:
    if not any(expected in value for value in values):
        failures.append(f"{label} missing substring: {expected!r}")


def validate_rollback_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(
        failures,
        report["recommended_strategy"],
        case["expected_strategy"],
        "recommended_strategy",
    )
    _expect_equal(
        failures,
        report["suggested_workflow"],
        case["expected_workflow"],
        "suggested_workflow",
    )
    for expected in case.get("expected_warning_contains", []):
        _expect_contains_in_collection(failures, report.get("warnings", []), expected, "warning")
    return failures


def validate_preferences_write_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    _expect_equal(failures, report["status"], case["expected_status"], "status")
    _expect_equal(failures, report["preferences"], case["expected_preferences"], "preferences")
    _expect_equal(failures, report["changed_fields"], case["expected_changed_fields"], "changed_fields")
    return failures


def validate_workspace_init_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    _expect_equal(failures, report["workspace_mode"], case["expected_mode"], "workspace_mode")
    _expect_equal(
        failures,
        report["recommended_next_workflow"],
        case["expected_next_workflow"],
        "recommended_next_workflow",
    )
    return failures


def validate_response_contract_case(case: dict, report: dict) -> list[str]:
    failures: list[str] = []
    _expect_equal(failures, report["status"], case["expected_status"], "status")
    if "expected_evidence_required" in case:
        _expect_equal(
            failures,
            report["evidence_required"],
            case["expected_evidence_required"],
            "evidence_required",
        )
    if "expected_evidence_mode" in case:
        _expect_equal(
            failures,
            report["checks"]["evidence_response"]["mode"],
            case["expected_evidence_mode"],
            "evidence_mode",
        )
    for expected in case.get("expected_finding_contains", []):
        _expect_contains_in_collection(failures, report.get("findings", []), expected, "finding")
    for expected in case.get("expected_warning_contains", []):
        _expect_contains_in_collection(failures, report.get("warnings", []), expected, "warning")
    return failures
