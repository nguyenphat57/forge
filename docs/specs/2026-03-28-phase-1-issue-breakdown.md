# Phase 1 Issue Breakdown
Created: 2026-03-28 | Status: Proposed
Inputs:
- [2026-03-28-phase-1-build-spec.md](C:\Users\Admin\.gemini\forge\docs\specs\2026-03-28-phase-1-build-spec.md)
- [2026-03-28-forge-solo-dev-roadmap.md](C:\Users\Admin\.gemini\forge\docs\plans\2026-03-28-forge-solo-dev-roadmap.md)

## Purpose

Break Phase 1 into implementation-ready issues that can be executed in order without lane-specific assumptions.

## Global Rules

- Epic 1 finishes before Epic 2; Epic 2 finishes before Epic 3.
- Schema and workflow land before integrations.
- Every issue ships with a direct test target.
- Medium and large work must end with durable artifacts, not chat-only state.

## Build Order

Epic 1 `doctor`:
1. workflow and report contract
2. environment checks
3. runtime and workspace checks
4. persistence, CLI polish, tests

Epic 2 `map-codebase`:
5. workflow and artifact schema
6. stack detection and structure scan
7. focus mode plus help-next integration
8. brownfield fixtures and tests

Epic 3 change artifacts:
9. artifact creation and pathing
10. status and verification recording
11. archive loop and continuity hooks
12. risk guard and route trigger integration

## Epic 1: `doctor`

### 1. doctor workflow and report contract
Goal: establish one stable workflow entry and one stable JSON contract.
Deliver:
- `packages/forge-core/workflows/operator/doctor.md`
- `packages/forge-core/scripts/doctor.py`
- report schema with `status`, `checks`, `warnings`, `blockers`, `remediations`, `workspace`, `timestamp`
Depends on: none
Done when:
- `doctor` runs in human mode and `--json`
- output shape is documented and testable
Tests: `packages/forge-core/tests/test_doctor.py`

### 2. environment checks
Goal: validate baseline toolchain before deeper Forge checks.
Deliver:
- `packages/forge-core/scripts/doctor_environment.py`
- checks for Python, Node or Bun when relevant, git, basic workspace root sanity
Depends on: 1
Done when:
- healthy fixture returns no blocker for toolchain
- broken fixture returns actionable remediation
Tests: extend `packages/forge-core/tests/test_doctor.py`

### 3. runtime and workspace checks
Goal: make runtime-tool and workspace health visible.
Deliver:
- `packages/forge-core/scripts/doctor_runtime.py`
- `packages/forge-core/scripts/doctor_workspace.py`
- checks for preferences readability, host binding sanity, `forge-browse` and `forge-design` registration, Playwright health when relevant, `.forge-artifacts/` write access
Depends on: 1, 2
Done when:
- browse or design misconfiguration appears as warning or blocker
- artifact write failure is surfaced clearly
Tests:
- extend `packages/forge-core/tests/test_doctor.py`
- add runtime-enabled and runtime-broken fixtures

### 4. persistence, CLI polish, tests
Goal: make `doctor` usable in repeat runs, CI, and support flows.
Deliver:
- `packages/forge-core/scripts/doctor_report.py`
- persistence to `.forge-artifacts/doctor/latest.json` and `.forge-artifacts/doctor/history/<timestamp>.json`
- optional `--strict` behavior
- doc updates in `packages/forge-core/references/tooling.md`
Depends on: 1, 2, 3
Done when:
- reruns update `latest.json` and append history cleanly
- `--strict` exits non-zero on blocker state
- docs show expected usage and output
Tests: add persistence and exit-code coverage in `packages/forge-core/tests/test_doctor.py`

## Epic 2: `map-codebase`

### 5. workflow and artifact schema
Goal: create one stable project-map contract before detection logic grows.
Deliver:
- `packages/forge-core/workflows/operator/map-codebase.md`
- `packages/forge-core/scripts/map_codebase.py`
- artifact schema for `summary.md`, `summary.json`, `stack.json`, `architecture.md`, `conventions.md`, `testing.md`, `integrations.md`, `risks.md`, `open-questions.md`
Depends on: Epic 1 complete
Done when:
- command creates the full artifact tree with placeholder-safe content
- artifact contract is documented and testable
Tests: `packages/forge-core/tests/test_map_codebase.py`

### 6. stack detection and structure scan
Goal: detect enough repo shape to make brownfield onboarding useful.
Deliver:
- `packages/forge-core/scripts/map_codebase_detect.py`
- `packages/forge-core/scripts/map_codebase_structure.py`
- detection for languages, frameworks, package managers, entrypoints, major folders, test harness hints, integration surfaces
Depends on: 5
Done when:
- at least two distinct brownfield fixtures produce sensible stack output
- summary content includes obvious risks and unknowns
Tests: extend `packages/forge-core/tests/test_map_codebase.py`

### 7. focus mode plus help-next integration
Goal: let later workflows consume the project map instead of rediscovering context.
Deliver:
- `packages/forge-core/scripts/map_codebase_focus.py`
- focus output at `.forge-artifacts/codebase/focus/<area>.md`
- read-path integration with `packages/forge-core/scripts/help_next_support.py` and `packages/forge-core/scripts/workflow_state_summary.py`
Depends on: 6
Done when:
- focused maps do not overwrite the full map
- `help` and `next` can reference map artifacts for suggestions
Tests:
- focus coverage in `packages/forge-core/tests/test_map_codebase.py`
- integration assertions in `packages/forge-core/tests/test_help_next.py`

### 8. brownfield fixtures and tests
Goal: harden `map-codebase` against real repo variety.
Deliver:
- expand fixtures under `packages/forge-core/tests/fixtures/`
- include at least one JS or TS web app and one Python backend app
Depends on: 5, 6, 7
Done when:
- rerun updates artifacts without corruption
- focused map and full map both pass on fixtures
Tests: fixture-backed regression coverage in `packages/forge-core/tests/test_map_codebase.py`

## Epic 3: change artifacts

### 9. artifact creation and pathing
Goal: create durable per-change folders before medium and large work begins.
Deliver:
- `packages/forge-core/workflows/execution/change.md`
- `packages/forge-core/scripts/change_artifacts.py`
- `packages/forge-core/scripts/change_artifacts_paths.py`
- active layout for `proposal.md`, `design.md`, `tasks.md`, `status.json`, `verification.md`
Depends on: Epic 2 complete
Done when:
- medium or large work can create a change folder before implementation
- slugs and paths are deterministic
Tests: `packages/forge-core/tests/test_change_artifacts.py`

### 10. status and verification recording
Goal: make change state and proof visible across sessions.
Deliver:
- `packages/forge-core/scripts/change_artifacts_status.py`
- status fields for state, timestamps, owner, verification summary
- verification template for checked items, latest result, residual risk
Depends on: 9
Done when:
- task execution can update `status.json`
- verification notes survive resume and rerun
Tests: extend `packages/forge-core/tests/test_change_artifacts.py`

### 11. archive loop and continuity hooks
Goal: turn shipped work into durable project knowledge.
Deliver:
- `packages/forge-core/scripts/change_artifacts_archive.py`
- archive root `.forge-artifacts/changes/archive/<date>-<slug>/`
- updates to `.brain/decisions.json` and `.brain/learnings.json` when warranted
- continuity hooks in `packages/forge-core/scripts/capture_continuity.py`
Depends on: 10
Done when:
- archived change preserves proposal, design, tasks, status, and verification
- continuity restore can reopen the latest active change
Tests: add archive coverage in `packages/forge-core/tests/test_change_artifacts.py`

### 12. risk guard and route trigger integration
Goal: ensure risky actions and medium-large work pass through the right control points.
Deliver:
- `packages/forge-core/scripts/change_guard.py`
- allow, warn, block classification for secret handling, deploy or production-adjacent actions, destructive filesystem actions
- route integration in `packages/forge-core/scripts/route_analysis.py` and `packages/forge-core/scripts/route_preview.py`
- optional quality integration in `packages/forge-core/scripts/record_quality_gate.py`
Depends on: 9, 10, 11
Done when:
- route analysis can require change artifacts for medium and large work
- at least one seeded risky action is blocked in tests
- guard output is human-readable and machine-readable
Tests:
- extend `packages/forge-core/tests/test_change_artifacts.py`
- add route assertions in `packages/forge-core/tests/test_route_preview.py`

## Release Criteria

This issue breakdown is ready to execute when:
- all 12 issues have explicit repo slices
- each issue has a direct test target
- epic dependencies are unambiguous
- no issue depends on lanes or templates

## Bottom Line

If these 12 issues land cleanly, Forge becomes useful on real repos before it becomes opinionated about stacks.
