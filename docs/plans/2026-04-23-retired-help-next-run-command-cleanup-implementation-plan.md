# Retired Help Next Run Command Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove command implementations and redundant support code tied to retired operator `help`, `next`, and `run` surfaces.
**Architecture:** `packages/forge-core/commands/` keeps only active core commands. Session continuity keeps its own minimal resume/save logic and must not import retired help/next commands.
**Tech Stack:** Python 3.13, pytest/unittest, Forge release bundle scripts.

## Source And Current State

- Source repo rejects operator `help`, `next`, and `run`, but `packages/forge-core/commands/resolve_help_next.py` and `packages/forge-core/commands/run_with_guidance.py` still ship.
- Release package matrix still requires those commands and their shared support modules.
- Smoke matrix, bundle verification preferences, docs, and tests still exercise retired help/next/run behavior.
- `forge-session-management` imports `resolve_help_next.build_report`, keeping the retired command alive indirectly.

## Desired End State

- `packages/forge-core/commands/resolve_help_next.py` and `packages/forge-core/commands/run_with_guidance.py` are removed.
- `packages/forge-core/shared/help_next_support.py` and `packages/forge-core/shared/run_guidance_support.py` are removed unless an active non-retired owner still needs them.
- `forge-session-management` uses owner-local session navigation helpers, not retired core commands.
- Package matrix, smoke matrix, docs, tests, and bundle verification stop requiring retired help/next/run artifacts.

## Out Of Scope

- Removing active session-management resume/save behavior.
- Removing workflow-state support used by active execution, planning, and session flows.
- Changing repo operator behavior beyond deleting dead implementation.

## File Structure And Responsibility Map

- `packages/forge-skills/session-management/commands/session_context_workspace.py`
  - Owner-local file/workspace inspection helpers needed by session resume/save.
- `packages/forge-skills/session-management/commands/session_context_reports.py`
  - Builds save/resume reports directly from session/workflow state without `resolve_help_next.py`.
- `packages/forge-skills/session-management/commands/session_context_io.py`
  - Owns JSON session loading helpers.
- `packages/forge-core/commands/`
  - Active core commands only; no help/next/run commands.
- `packages/forge-core/shared/`
  - Shared active runtime only; no help/next/run support modules.
- `docs/release/package-matrix.json`, `packages/forge-core/commands/verify_bundle.py`, `packages/forge-core/tools/smoke_matrix_suites.py`
  - Drop retired command requirements and suites.

## Implementation Tasks

### Task 1: RED retired command absence

- [x] Step 1: Add command absence contract
  - Files: `packages/forge-core/tests/test_contracts.py`
  - Change: assert retired help/next/run commands and support modules are absent from core.
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py::BundleContractTests::test_runtime_commands_are_owned_in_place -q` -> FAIL because retired files still exist.

### Task 2: Decouple session-management

- [x] Step 1: Add session-owned workspace helpers
  - Files: `packages/forge-skills/session-management/commands/session_context_workspace.py`, `packages/forge-skills/session-management/commands/session_context_io.py`
  - Change: move only needed JSON, git status, handover, and latest-artifact helpers into session-management.
  - Proof: `python -m pytest packages/forge-core/tests/test_session_context.py -q` -> PASS after report wiring.

- [x] Step 2: Remove `resolve_help_next` dependency
  - Files: `packages/forge-skills/session-management/commands/session_context_reports.py`
  - Change: build session navigator data directly from workflow-state and session files.
  - Proof: `python -m pytest packages/forge-core/tests/test_session_context.py -q` -> PASS.

### Task 3: Delete retired commands and suites

- [x] Step 1: Remove retired command and support files
  - Files: `packages/forge-core/commands/resolve_help_next.py`, `packages/forge-core/commands/run_with_guidance.py`, `packages/forge-core/shared/help_next_support.py`, `packages/forge-core/shared/run_guidance_support.py`
  - Change: delete files after active imports are gone.
  - Proof: `rg -n "resolve_help_next|run_with_guidance|help_next_support|run_guidance_support" packages scripts tests docs -g "!docs/plans/**"` shows only intentional historical wording or no active references.

- [x] Step 2: Remove tests and smoke cases for retired surfaces
  - Files: `packages/forge-core/tests/test_help_next.py`, `packages/forge-core/tests/test_help_next_workflow_state.py`, `packages/forge-core/tests/test_run_workflow.py`, retired help-next fixtures, smoke matrix suites/validators/cases.
  - Change: delete retired tests/fixtures and remove suite entries.
  - Proof: `python -m pytest packages/forge-core/tests/test_session_context.py packages/forge-core/tests/test_contracts.py -q` -> PASS.

### Task 4: Update release/docs/build contracts

- [x] Step 1: Update package and bundle verification contracts
  - Files: `docs/release/package-matrix.json`, `packages/forge-core/commands/verify_bundle.py`, release tests if needed.
  - Change: remove retired required paths and preferred dist tests.
  - Proof: `python scripts/build_release.py --force --format json` -> PASS.

- [x] Step 2: Update docs that still advertise retired commands
  - Files: `docs/current/kernel-tooling.md`, `docs/current/smoke-tests.md`, `packages/forge-core/workflows/operator/references/*.md`, architecture/contract tests as needed.
  - Change: remove help/next/run command references or mark them as retired only when the doc is historical.
  - Proof: content search excludes active docs from retired command references.

### Task 5: Final verification

- [x] Step 1: Run targeted and fast verification
  - Files: none
  - Proof:
    - `python -m pytest packages/forge-core/tests/test_contracts.py::BundleContractTests::test_runtime_commands_are_owned_in_place packages/forge-core/tests/test_session_context.py -q`
    - `python scripts/generate_host_artifacts.py --check --format json`
    - `python scripts/generate_overlay_skills.py --check --format json`
    - `python scripts/verify_repo.py --profile fast`

## Acceptance Criteria

- Core commands directory no longer contains `resolve_help_next.py` or `run_with_guidance.py`.
- Active package matrix no longer ships retired help/next/run command paths.
- Session-management remains functional without importing retired core commands.
- Fast verification passes.

## Risks And Rollback

- Risk: session resume/save loses recommendation quality formerly supplied by `resolve_help_next.py`.
  - Rollback: keep recommendation logic inside session-management, but do not restore retired command entrypoints.
- Risk: release tests still expect historical help-next fixture coverage.
  - Rollback: update contract tests to assert the retired surface is absent instead of exercised.

## Execution Mode

- Chosen mode: Inline Execution.
- Reason: cleanup crosses commands, session owner, tests, docs, and release matrix in one tightly coupled slice.
