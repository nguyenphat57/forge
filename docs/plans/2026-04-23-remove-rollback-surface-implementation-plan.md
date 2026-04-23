# Remove Rollback Surface Implementation Plan

Status: implemented

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `rollback` completely from the current Forge product line as a separate follow-up to the repo-first runtime cleanup.
**Architecture:** Remove the rollback planner, wrappers, registries, generated host artifacts, current docs, and dedicated tests so rollback is no longer a public or hidden current Forge surface.
**Tech Stack:** Python operator/build scripts, markdown docs and generated overlays, unittest/pytest release and contract coverage.

## Source And Current State

- `rollback` is still a public repo operator action in `scripts/repo_operator.py`.
- `rollback` still exists in core and host operator registries, current docs, generated wrappers, overlay packaging, and smoke tests.
- `packages/forge-core/scripts/resolve_rollback.py` still ships as a dedicated planner with its own guidance and test surface.

## Desired End State

- `rollback` no longer exists as a public source-repo or host action.
- No current wrapper, planner, generated artifact, packaging manifest, or current doc advertises rollback as an active Forge capability.
- No hidden maintainer-only rollback planner remains in the current tree.

## Out Of Scope

- Replacing rollback with a new public action.
- Removing generic non-operator uses of the word `rollback` where it only describes risk or recovery concepts.
- Editing archive/history docs unless an active test requires archival relocation.

## File Structure And Responsibility Map

- `scripts/repo_operator.py`
  - source-repo public action contract.
- `packages/forge-core/data/orchestrator-registry.json`
  - core repo and host operator-surface contract.
- `packages/forge-core/workflows/operator/` and `packages/forge-core/scripts/`
  - core compatibility wrappers and planner scripts.
- `packages/forge-codex/overlay/` and `packages/forge-antigravity/overlay/`
  - host overlay wrappers, registries, generated docs, and bootstrap artifacts.
- `docs/current/`
  - current public maintainer/operator story.
- `tests/`
  - repo operator, registry, generated-artifact, overlay, release, and current-doc contract coverage.

## Implementation Tasks

### Task 1: Lock the removed rollback contract with RED

- [ ] Step 1: Update repo/operator/host contract tests to expect no rollback action
  - Files: `tests/test_repo_operator_script_shims.py`, `tests/test_operator_surface_registry.py`, `tests/test_host_artifact_generation.py`
  - Change: assert `rollback` is absent from repo and host action sets and that `repo_operator.py rollback` is rejected as unsupported
  - Proof: `python -m pytest tests/test_repo_operator_script_shims.py tests/test_operator_surface_registry.py tests/test_host_artifact_generation.py -q` -> FAIL because rollback is still in the current contract
  - Notes: keep `delegate` on Codex host surface intact

- [ ] Step 2: Update release and current-doc contract tests to expect no rollback wrapper or planner
  - Files: `tests/release_repo_test_overlays.py`, `tests/release_repo_test_contracts.py`, `packages/forge-core/tests/test_contracts.py`
  - Change: remove `rollback` wrapper and `rollback-guidance` from required-path expectations and assert current docs no longer advertise rollback as an active surface
  - Proof: `python -m pytest tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py packages/forge-core/tests/test_contracts.py -q` -> FAIL because rollback assets and docs still exist
  - Notes: generic risk-language mentions may remain outside active operator/public-surface assertions

### Task 2: Remove rollback from the actual product surface

- [ ] Step 1: Remove repo action and core planner/wrapper assets
  - Files: `scripts/repo_operator.py`, `packages/forge-core/data/orchestrator-registry.json`, `packages/forge-core/workflows/operator/rollback.md`, `packages/forge-core/workflows/operator/references/rollback-guidance.md`, `packages/forge-core/scripts/resolve_rollback.py`
  - Change: delete rollback from the repo operator dispatch and remove the core rollback workflow/planner assets entirely
  - Proof: rerun `python -m pytest tests/test_repo_operator_script_shims.py tests/test_operator_surface_registry.py tests/test_host_artifact_generation.py -q`
  - Notes: no compatibility alias or hidden internal fallback should survive

- [ ] Step 2: Remove host overlay rollback wiring and generated wrapper expectations
  - Files: `packages/forge-codex/overlay/**`, `packages/forge-antigravity/overlay/**`, `scripts/operator_surface_support.py`, generated host-artifact source metadata under `docs/architecture/generated-host-artifacts/**`
  - Change: remove rollback from overlay registries, wrapper generation, public bootstrap lists, operator-surface docs, and packaged overlay files
  - Proof: rerun `python -m pytest tests/test_operator_surface_registry.py tests/test_host_artifact_generation.py tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py -q`
  - Notes: regenerate host artifacts from source rather than hand-editing generated outputs inconsistently

- [ ] Step 3: Remove current-doc rollback story and smoke scenarios
  - Files: `docs/current/operator-surface.md`, `docs/current/smoke-tests.md`, `docs/current/smoke-test-checklist.md`, `docs/current/kernel-tooling.md`, any active current doc that still presents rollback as a public surface
  - Change: remove rollback from public action lists, wrapper references, and active smoke expectations
  - Proof: rerun `python -m pytest tests/release_repo_test_contracts.py packages/forge-core/tests/test_contracts.py tests/test_operator_surface_registry.py -q`
  - Notes: do not scrub rollback from archive/history or generic design-risk prose

### Task 3: Clean dedicated rollback-only verification and packaging fallout

- [ ] Step 1: Remove rollback-only fixtures, smoke coverage, and build expectations
  - Files: rollback-specific tests/fixtures under `packages/forge-core/tests/` and `packages/forge-core/scripts/` plus release/build expectations that still require rollback artifacts
  - Change: delete dedicated rollback planner tests and update suite registration/build expectations so no removed asset is referenced
  - Proof: `python -m pytest tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py tests/test_repo_operator_script_shims.py tests/test_operator_surface_registry.py tests/test_host_artifact_generation.py packages/forge-core/tests/test_contracts.py -q`
  - Notes: only remove coverage that exists solely for the deleted rollback surface

- [ ] Step 2: Run the broader release/build baseline
  - Files: none
  - Change: verify generated artifacts, dist packaging, and release contracts still build cleanly after rollback removal
  - Proof: `python scripts/build_release.py --format json` and `python -m pytest tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py tests/test_repo_operator_script_shims.py tests/test_operator_surface_registry.py tests/test_host_artifact_generation.py packages/forge-core/tests/test_contracts.py -q`
  - Notes: if build outputs change, inspect the generated manifests rather than weakening the baseline

## Acceptance Criteria

- `scripts/repo_operator.py` no longer supports `rollback`.
- Core and host operator-surface registries no longer expose rollback.
- No shipped core or overlay wrapper/package path requires `workflows/operator/rollback.md`.
- `resolve_rollback.py` and its dedicated current guidance/tests are gone.
- Current public docs and generated bootstrap docs no longer list rollback as an explicit Forge action.

## Verification

- `python -m pytest tests/test_repo_operator_script_shims.py tests/test_operator_surface_registry.py tests/test_host_artifact_generation.py -q`
- `python -m pytest tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py packages/forge-core/tests/test_contracts.py -q`
- `python scripts/build_release.py --format json`
- `rg -n "rollback" scripts packages/forge-core packages/forge-codex/overlay packages/forge-antigravity/overlay docs/current tests`

## Risks And Rollback

- Biggest risk: leaving stale generated-artifact metadata or overlay registry entries that still require deleted rollback wrappers.
- Secondary risk: removing rollback from current docs but not from bootstrap/generated outputs, causing contract drift.
- Rollback: revert the repo operator, registry, wrapper, generated-artifact, and current-doc cleanup together, then rerun the same verification packet; do not keep a half-removed rollback surface.

## Execution Mode

Recommended execution order:

1. RED on repo/operator/host contract tests.
2. Remove repo action and core planner/wrapper assets.
3. Remove host overlay/generated-artifact wiring and current-doc references.
4. Run release/build regression baseline.

Plan complete and saved to `docs/plans/2026-04-23-remove-rollback-surface-implementation-plan.md`. Choose execution mode:
1. Subagent-Driven - use forge-subagent-driven-development
2. Inline Execution - use forge-executing-plans
