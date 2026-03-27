from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
WORKSPACES_DIR = FIXTURES_DIR / "workspaces"
FORGE_HOMES_DIR = FIXTURES_DIR / "forge-homes"
RUN_HELPERS_DIR = FIXTURES_DIR / "run_helpers"

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
RESPONSE_CONTRACT_CASES = json.loads((FIXTURES_DIR / "response_contract_cases.json").read_text(encoding="utf-8"))


def workspace_path(name: str) -> Path:
    return WORKSPACES_DIR / name


def forge_home_path(name: str) -> Path:
    return FORGE_HOMES_DIR / name
