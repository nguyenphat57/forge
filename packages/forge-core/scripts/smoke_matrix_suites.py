from __future__ import annotations

import json
import sys

from smoke_matrix_cases import (
    BUMP_CASES,
    ERROR_TRANSLATION_CASES,
    HELP_NEXT_CASES,
    PREFERENCES_CASES,
    PREFERENCES_WRITE_CASES,
    RESPONSE_CONTRACT_CASES,
    ROOT_DIR,
    ROUTER_CASES,
    RUN_CASES,
    WORKSPACE_INIT_CASES,
    forge_home_path,
    workspace_path,
)
from smoke_matrix_runtime import case_failure, case_result, resolve_run_command, run_command
from smoke_matrix_validators import (
    validate_bump_case,
    validate_error_translation_case,
    validate_help_next_case,
    validate_preferences_case,
    validate_router_case,
    validate_run_case,
)
from smoke_matrix_validators_tail import (
    validate_preferences_write_case,
    validate_response_contract_case,
    validate_workspace_init_case,
)


def _load_report(completed_output: str) -> dict:
    return json.loads(completed_output)


def _run_json_suite(
    suite: str,
    cases: list[dict],
    *,
    command_builder,
    validator,
    allowed_returncodes: set[int] | None = None,
    failure_label: str = "command exited",
) -> list[dict]:
    allowed_codes = allowed_returncodes or {0}
    results: list[dict] = []
    for case in cases:
        command, env = command_builder(case)
        completed = run_command(command, env=env)
        if completed.returncode not in allowed_codes:
            output = completed.stderr or completed.stdout
            results.append(
                case_failure(
                    suite,
                    case["name"],
                    f"{failure_label} {completed.returncode}",
                    output,
                )
            )
            continue

        report = _load_report(completed.stdout)
        results.append(case_result(suite, case["name"], validator(case, report)))
    return results


def run_router_suite() -> list[dict]:
    router_script = ROOT_DIR / "scripts" / "check_workspace_router.py"
    return _run_json_suite(
        "router-check",
        ROUTER_CASES,
        command_builder=lambda case: (
            [sys.executable, str(router_script), str(workspace_path(case["workspace_fixture"])), "--format", "json"],
            None,
        ),
        validator=validate_router_case,
        allowed_returncodes={0, 1},
        failure_label="unexpected exit code",
    )


def run_preferences_suite() -> list[dict]:
    preferences_script = ROOT_DIR / "scripts" / "repo_operator.py"
    return _run_json_suite(
        "preferences",
        PREFERENCES_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(preferences_script),
                "customize",
                "--workspace",
                str(workspace_path(case["workspace_fixture"])),
                "--format",
                "json",
            ],
            {"FORGE_HOME": str(forge_home_path(case["forge_home_fixture"]))} if case.get("forge_home_fixture") else None,
        ),
        validator=validate_preferences_case,
    )


def run_help_next_suite() -> list[dict]:
    navigator_script = ROOT_DIR / "scripts" / "repo_operator.py"
    return _run_json_suite(
        "help-next",
        HELP_NEXT_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(navigator_script),
                case["mode"],
                "--workspace",
                str(workspace_path(case["workspace_fixture"])),
                "--format",
                "json",
            ],
            None,
        ),
        validator=validate_help_next_case,
    )


def run_run_suite() -> list[dict]:
    run_script = ROOT_DIR / "scripts" / "repo_operator.py"
    return _run_json_suite(
        "run",
        RUN_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(run_script),
                "run",
                "--workspace",
                str(workspace_path(case["workspace_fixture"])),
                "--timeout-ms",
                str(case["timeout_ms"]),
                "--format",
                "json",
                "--",
                *resolve_run_command(case["command"]),
            ],
            None,
        ),
        validator=validate_run_case,
        allowed_returncodes={0, 1},
        failure_label="unexpected exit code",
    )


def run_error_translation_suite() -> list[dict]:
    translate_script = ROOT_DIR / "scripts" / "translate_error.py"
    return _run_json_suite(
        "error-translation",
        ERROR_TRANSLATION_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(translate_script),
                "--error-text",
                case["error_text"],
                "--format",
                "json",
            ],
            None,
        ),
        validator=validate_error_translation_case,
    )


def run_bump_suite() -> list[dict]:
    bump_script = ROOT_DIR / "scripts" / "repo_operator.py"
    return _run_json_suite(
        "bump",
        BUMP_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(bump_script),
                "bump",
                "--workspace",
                str(workspace_path(case["workspace_fixture"])),
                case["bump"],
                "--format",
                "json",
            ],
            None,
        ),
        validator=validate_bump_case,
    )


def run_preferences_write_suite() -> list[dict]:
    write_script = ROOT_DIR / "scripts" / "repo_operator.py"
    return _run_json_suite(
        "preferences-write",
        PREFERENCES_WRITE_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(write_script),
                "customize",
                "--workspace",
                str(workspace_path(case["workspace_fixture"])),
                "--format",
                "json",
                *case["args"],
            ],
            {"FORGE_HOME": str(forge_home_path(case["forge_home_fixture"]))} if case.get("forge_home_fixture") else None,
        ),
        validator=validate_preferences_write_case,
    )


def run_workspace_init_suite() -> list[dict]:
    init_script = ROOT_DIR / "scripts" / "repo_operator.py"
    return _run_json_suite(
        "workspace-init",
        WORKSPACE_INIT_CASES,
        command_builder=lambda case: (
            [
                sys.executable,
                str(init_script),
                "init",
                "--workspace",
                str(workspace_path(case["workspace_fixture"])),
                "--format",
                "json",
                *case["args"],
            ],
            {"FORGE_HOME": str(forge_home_path(case["forge_home_fixture"]))} if case.get("forge_home_fixture") else None,
        ),
        validator=validate_workspace_init_case,
    )


def run_response_contract_suite() -> list[dict]:
    contract_script = ROOT_DIR / "scripts" / "check_response_contract.py"
    return _run_json_suite(
        "response-contract",
        RESPONSE_CONTRACT_CASES,
        command_builder=lambda case: (
            [sys.executable, str(contract_script), "--format", "json", *case["args"]],
            None,
        ),
        validator=validate_response_contract_case,
        allowed_returncodes={0, 1},
        failure_label="unexpected exit code",
    )


SUITE_RUNNERS = {
    "router-check": run_router_suite,
    "preferences": run_preferences_suite,
    "help-next": run_help_next_suite,
    "run": run_run_suite,
    "error-translation": run_error_translation_suite,
    "bump": run_bump_suite,
    "preferences-write": run_preferences_write_suite,
    "workspace-init": run_workspace_init_suite,
    "response-contract": run_response_contract_suite,
}
