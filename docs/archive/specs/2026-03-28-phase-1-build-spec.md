# Phase 1 Build Spec: Doctor, Map-Codebase, Change Artifacts
Created: 2026-03-28 | Status: Proposed
Inputs:
- [2026-03-28-forge-solo-dev-roadmap.md](../plans/2026-03-28-forge-solo-dev-roadmap.md)
- [2026-03-28-solo-dev-ecosystem-review.md](../audits/2026-03-28-solo-dev-ecosystem-review.md)

## Purpose

Define the first implementation slice that makes Forge practical on real repos before any lane-specific depth exists.

In scope:
1. `doctor`
2. `map-codebase`
3. change artifacts plus archive loop

Out of scope:
- lane presets
- starter templates
- dashboard
- advanced canary

Phase 1 loop:

`doctor -> map-codebase -> change-start -> implement -> verify -> archive`

## Shared Rules

- Natural language first; aliases stay optional.
- Brownfield support matters as much as greenfield support.
- Medium and large work must leave durable artifacts.
- Small low-risk work may skip change artifacts.
- No completion claims without fresh evidence.
- Docs-only work uses path, content, or diff verification.
- File-backed artifacts win over chat-only memory.
- Risky actions should pass an allow, warn, or block guard before tool execution.

## Workstream 1: `doctor`

Problem:
- Forge currently assumes too much about the local environment.

User flows:
1. New user installs Forge and runs `doctor`.
2. Existing user needs to debug browse, design, or host wiring.
3. CI or support wants a machine-readable health report.

User surface:
- natural language: `run doctor on this workspace`
- optional alias: `doctor`
- modes: default, `--json`, `--strict`

Required checks:
- Python
- Node or Bun when relevant
- git
- workspace root sanity
- preferences readability
- host binding sanity
- `forge-browse` and `forge-design` registration
- Playwright or browser health when browse is installed
- write access for `.forge-artifacts/`

Output contract:
- human summary with overall status, checks, and remediation steps
- JSON with `status`, `checks`, `warnings`, `blockers`, `remediations`, `workspace`, `timestamp`
- artifacts:
  - `.forge-artifacts/doctor/latest.json`
  - `.forge-artifacts/doctor/history/<timestamp>.json`

Repo slices:
- workflow: `packages/forge-core/workflows/operator/doctor.md`
- scripts:
  - `packages/forge-core/scripts/doctor.py`
  - `packages/forge-core/scripts/doctor_environment.py`
  - `packages/forge-core/scripts/doctor_runtime.py`
  - `packages/forge-core/scripts/doctor_workspace.py`
  - `packages/forge-core/scripts/doctor_report.py`
- likely touched:
  - `packages/forge-core/references/tooling.md`
  - `packages/forge-core/scripts/runtime_tool_support.py`
  - `packages/forge-core/tests/support.py`
- tests:
  - `packages/forge-core/tests/test_doctor.py`
  - fixtures for healthy, warning, and blocked states

Non-goals:
- no auto-fix mode
- no network-heavy diagnosis
- no performance benchmarking

Verification:
- healthy fixture returns `healthy`
- broken fixture returns actionable blockers
- JSON output is deterministic
- artifact writes are rerunnable

Exit criteria:
- a new user can understand what is broken in under two minutes
- CI and support can consume the JSON output without scraping text

## Workstream 2: `map-codebase`

Problem:
- Forge still learns too much from live chat and too little from a durable project map.

User flows:
1. User opens an unfamiliar repo and asks Forge what it is.
2. User wants a scoped map for `api`, `auth`, `frontend`, or `deploy`.
3. Later workflows need a shared project map instead of rediscovering the same context.

User surface:
- natural language: `map this codebase`
- optional alias: `map-codebase`
- modes: full map, focused map, refresh

Output contract:
- root: `.forge-artifacts/codebase/`
- required files:
  - `summary.md`
  - `summary.json`
  - `stack.json`
  - `architecture.md`
  - `conventions.md`
  - `testing.md`
  - `integrations.md`
  - `risks.md`
  - `open-questions.md`
- optional focus files:
  - `.forge-artifacts/codebase/focus/<area>.md`

Minimum content:
- languages, frameworks, package managers, runtime assumptions
- entrypoints and major folders
- data access and integration surfaces
- test harness and verification commands
- obvious risks and unknowns
- suggested next actions

Repo slices:
- workflow: `packages/forge-core/workflows/operator/map-codebase.md`
- scripts:
  - `packages/forge-core/scripts/map_codebase.py`
  - `packages/forge-core/scripts/map_codebase_detect.py`
  - `packages/forge-core/scripts/map_codebase_structure.py`
  - `packages/forge-core/scripts/map_codebase_focus.py`
  - `packages/forge-core/scripts/map_codebase_report.py`
- likely touched:
  - `packages/forge-core/scripts/help_next_support.py`
  - `packages/forge-core/scripts/workflow_state_summary.py`
  - `packages/forge-core/references/help-next.md`
- tests:
  - `packages/forge-core/tests/test_map_codebase.py`
  - brownfield fixtures across at least two stacks

Non-goals:
- no deep semantic index
- no full architecture diagram generation
- no claim of complete code understanding

Verification:
- sample brownfield repo produces readable artifacts
- rerun updates artifacts without corruption
- focused map does not overwrite full map unexpectedly
- `help` and `next` can consume the map outputs

Exit criteria:
- Forge can explain an existing repo before editing
- later workflows reuse the map instead of repeating discovery work

## Workstream 3: Change Artifacts Plus Archive Loop

Problem:
- Medium and large work currently risks vanishing into chat history.

Trigger rule:
- required for route-analysis medium and large work
- optional for low-risk small work
- manually creatable when the user wants a durable spec trail

User flows:
1. Forge creates a change folder before a medium feature starts.
2. Work pauses and resumes later without losing plan, design, and verification state.
3. After shipping, Forge archives the change and updates durable knowledge.

User surface:
- natural language: `start a change for add dark mode`
- optional aliases: `change-start`, `change-status`, `change-archive`

Artifact layout:
- active root: `.forge-artifacts/changes/active/<slug>/`
- required files:
  - `proposal.md`
  - `design.md`
  - `tasks.md`
  - `status.json`
  - `verification.md`
- archive root: `.forge-artifacts/changes/archive/<date>-<slug>/`

Archive effects:
- preserve final change artifacts in archive
- update `.brain/decisions.json` when architecture changed
- update `.brain/learnings.json` when reusable lessons emerged

Minimum content:
- `proposal.md`: why, scope, non-goals
- `design.md`: affected areas, approach, risks, open questions
- `tasks.md`: ordered checklist plus verification method per task group
- `status.json`: state, owner, timestamps, verification summary
- `verification.md`: what was checked, latest result, residual risk

Guard behavior:
- classify risky actions as `allow`, `warn`, or `block`
- initial v1 risk classes:
  - secret handling
  - deploy or production-adjacent actions
  - destructive filesystem actions

Repo slices:
- workflow: `packages/forge-core/workflows/execution/change.md`
- scripts:
  - `packages/forge-core/scripts/change_artifacts.py`
  - `packages/forge-core/scripts/change_artifacts_paths.py`
  - `packages/forge-core/scripts/change_artifacts_archive.py`
  - `packages/forge-core/scripts/change_artifacts_status.py`
  - `packages/forge-core/scripts/change_guard.py`
- likely touched:
  - `packages/forge-core/scripts/route_analysis.py`
  - `packages/forge-core/scripts/route_preview.py`
  - `packages/forge-core/scripts/capture_continuity.py`
  - `packages/forge-core/scripts/record_quality_gate.py`
  - `packages/forge-core/references/execution-delivery.md`
- tests:
  - `packages/forge-core/tests/test_change_artifacts.py`
  - fixtures for medium, large, and archived changes

Non-goals:
- no full OpenSpec-style command matrix
- no heavy markdown ceremony for small tasks
- no automatic mutation of product docs beyond decisions and learnings

Verification:
- medium task creates artifacts before implementation starts
- archived change preserves proposal, design, tasks, and verification history
- continuity restore can reopen an active change correctly
- guard blocks at least one seeded risky action in tests

Exit criteria:
- medium and large work survives after the chat window is gone
- Forge can resume an unfinished feature with clear prior state
- shipped work leaves durable project knowledge behind

## Sequencing

Build order:
1. `doctor`
2. `map-codebase`
3. change artifacts core
4. archive loop
5. initial risk guard

Reason:
- `doctor` makes the environment legible
- `map-codebase` makes the repo legible
- change artifacts make the work legible

## Verification Plan

Docs verification:
- file exists at `docs/specs/2026-03-28-phase-1-build-spec.md`
- content references roadmap and audit inputs

Implementation readiness:
- every workstream names workflow, scripts, tests, non-goals, and exit criteria
- no workstream depends on lane-specific assumptions

## Bottom Line

If Forge ships these three workstreams well, it becomes useful before any lane exists. That is the right standard for Phase 1.
