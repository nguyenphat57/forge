# Forge Core Cleanup Implementation Plan

Status: implemented

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `packages/forge-core` materially smaller and cleaner by removing cache/build residue, archiving dead historical surfaces, and shrinking route-era legacy that no longer belongs on the current maintainer path.
**Architecture:** Keep the current split-skill, operator-only workflow contract intact while moving retired or low-value residue out of the active `forge-core` tree.
**Tech Stack:** Python scripts, markdown references, pytest/unittest contract suite.

## Source And Current State

- `packages/forge-core/workflows/` is now operator-only, but the package still carries non-trivial historical residue in references, scripts, and tests.
- `packages/forge-core/.pytest_cache/`, `packages/forge-core/scripts/__pycache__/`, and `packages/forge-core/tests/__pycache__/` are generated residue and should not be source-controlled.
- `packages/forge-core/scripts/workspace_signals.py` currently has no live inbound references in the active repo.
- Five test files are explicitly marked historical via `Archived:` skip messages:
  - `packages/forge-core/tests/test_router_matrix.py`
  - `packages/forge-core/tests/test_route_complexity_safety.py`
  - `packages/forge-core/tests/test_route_matrix.py`
  - `packages/forge-core/tests/test_route_preview.py`
  - `packages/forge-core/tests/test_superpowers_route_preview.py`
- Several reference files are no longer part of the current maintainer reading path and appear to survive mainly as stale legacy surfaces:
  - `packages/forge-core/references/companion-skill-contract.md`
  - `packages/forge-core/references/companion-routing-smoke-tests.md`
  - `packages/forge-core/references/canary-rollout.md`
  - `packages/forge-core/references/extension-presets.md`
  - `packages/forge-core/references/frontend-stack-profiles.md`
- `packages/forge-core/references/tooling.md` remains a catch-all monolith even though `reference-map.md` and `kernel-tooling.md` are already the current maintainer entrypoints.
- The route-era script cluster under `packages/forge-core/scripts/route*.py` still contains 17 files. It is no longer the public contract, but workflow-state and a few support paths still depend on parts of it.

## Desired End State

- `packages/forge-core` contains no generated cache residue.
- Historical skipped tests no longer live in the active test package.
- Dead or stale reference docs move to archive or are deleted after contract updates.
- `tooling.md` becomes a thin pointer or is absorbed into `kernel-tooling.md`.
- Route-era logic is reduced to the smallest internal compatibility core needed by workflow-state and contract tooling.
- The active `forge-core` tree is clearly current-contract only, with archive-worthy material moved out of the active package.

## Out Of Scope

- Changing the split-skill public contract.
- Removing the operator-only workflow wrappers added in the current tranche.
- Replacing workflow-state or help/next behavior.
- Reworking adapter overlays beyond fallout needed for `forge-core` cleanup.

## File Structure And Responsibility Map

- `packages/forge-core/`
  - `scripts/`: deterministic engine and compatibility helpers that are still live.
  - `references/`: only current maintainer references that still support the live kernel contract.
  - `tests/`: only active contract and behavior tests.
  - `workflows/`: operator-only compatibility wrappers.
- `docs/archive/`
  - destination for historical references and tests that are intentionally retained for archaeology rather than active maintenance.

## Implementation Tasks

### Task 1: Remove generated residue from `forge-core`

- [x] Step 1: Add ignore/clean-up coverage for generated residue
  - Files: `.gitignore`, `packages/forge-core/.pytest_cache/`, `packages/forge-core/scripts/__pycache__/`, `packages/forge-core/tests/__pycache__/`
  - Change: ensure cache and bytecode directories are ignored and removed from the tracked tree
  - Proof: `git status --short packages/forge-core` no longer shows tracked cache residue
  - Notes: this is a pure cleanliness slice

- [x] Step 2: Add a regression test or content check for forbidden residue
  - Files: `packages/forge-core/tests/test_contracts.py`
  - Change: assert `forge-core` does not contain `.pytest_cache` or `__pycache__` directories
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py -q` -> FAIL before cleanup for the right reason, then PASS
  - Notes: keep the assertion narrow and mechanical

### Task 2: Remove dead active-package tests

- [x] Step 1: Add a contract check for archived route-era tests
  - Files: `packages/forge-core/tests/test_contracts.py`
  - Change: assert the active test package does not include files whose only purpose is archived route-preview coverage
  - Proof: targeted test command fails while the files still exist
  - Notes: cover the five known `Archived:` files explicitly

- [x] Step 2: Move or delete the five archived route-era tests
  - Files: `packages/forge-core/tests/test_router_matrix.py`, `packages/forge-core/tests/test_route_complexity_safety.py`, `packages/forge-core/tests/test_route_matrix.py`, `packages/forge-core/tests/test_route_preview.py`, `packages/forge-core/tests/test_superpowers_route_preview.py`
  - Change: remove them from the active test package; archive only if historical retention is still desired
  - Proof: targeted contract test passes and `python -m pytest packages/forge-core/tests -q` still completes
  - Notes: do not move active route-delegation or workflow-state tests

### Task 3: Archive stale companion/canary references

- [x] Step 1: Update live reference pointers first
  - Files: `packages/forge-core/references/reference-map.md`
  - Change: remove current-contract reading-path references to stale companion/canary docs
  - Proof: targeted doc/content check shows the old filenames no longer appear in live reading paths
  - Notes: keep `reference-map.md` focused on current maintainer entrypoints

- [x] Step 2: Move stale docs out of active `forge-core/references/`
  - Files: `packages/forge-core/references/companion-skill-contract.md`, `packages/forge-core/references/companion-routing-smoke-tests.md`, `packages/forge-core/references/canary-rollout.md`
  - Change: archive or delete these files after live references are removed
  - Proof: repo-wide search outside `docs/archive/**` finds no live references to them
  - Notes: these are historical by current contract, not active kernel docs

### Task 4: Decide and clean optional stale references

- [x] Step 1: Audit low-value survivors
  - Files: `packages/forge-core/references/extension-presets.md`, `packages/forge-core/references/frontend-stack-profiles.md`, `packages/forge-core/references/backend-briefs.md`, `packages/forge-core/references/ui-briefs.md`, `packages/forge-core/references/ui-progress.md`, `packages/forge-core/references/tooling.md`
  - Change: classify each as keep, merge, archive, or delete
  - Proof: written classification in the cleanup PR or follow-up spec
  - Notes: `backend-briefs.md`, `ui-briefs.md`, and `ui-progress.md` still have live script ties; do not delete them without collapsing those scripts too
  - Execution note: `extension-presets.md` and `frontend-stack-profiles.md` had no live inbound maintainer-path references outside `reference-map.md` and were archived; `backend-briefs.md`, `ui-briefs.md`, and `ui-progress.md` stay active because shipped checker/runtime guidance still points at them; `tooling.md` stayed active but was reduced to a pointer.

- [x] Step 2: Shrink or absorb `tooling.md`
  - Files: `packages/forge-core/references/tooling.md`, `packages/forge-core/references/kernel-tooling.md`
  - Change: either replace `tooling.md` with a thin pointer or merge the current-contract content into `kernel-tooling.md`
  - Proof: `tooling.md` line count drops materially or the file disappears with updated references
  - Notes: avoid leaving two overlapping maintainer monoliths
  - Execution note: `tooling.md` was retained as a sub-40-line pointer to `kernel-tooling.md`, `reference-map.md`, and the brief/progress references that still matter.

### Task 5: Remove dead utility scripts

- [x] Step 1: Add proof for the obvious dead utility
  - Files: `packages/forge-core/tests/test_contracts.py`, `packages/forge-core/scripts/workspace_signals.py`
  - Change: assert dead standalone utility files do not remain in the active script tree when they have no live references
  - Proof: targeted test fails while `workspace_signals.py` exists, then passes after removal
  - Notes: verify no dynamic import path is hiding before deletion
  - Execution note: contract coverage now explicitly asserts `workspace_signals.py` is absent from the active script tree.

- [x] Step 2: Delete `workspace_signals.py`
  - Files: `packages/forge-core/scripts/workspace_signals.py`
  - Change: remove the file
  - Proof: repo-wide search outside archive/dist finds no live references and the contract test passes
  - Notes: keep this slice separate from the route-era reduction
  - Execution note: `workspace_signals.py` was removed during tranche 1 and stays locked out by `test_contracts.py`.

### Task 6: Collapse the route-era legacy cluster

- [x] Step 1: Split the route cluster into required vs retired internals
  - Files: `packages/forge-core/scripts/route*.py`, `packages/forge-core/scripts/skill_routing.py`, `packages/forge-core/scripts/workflow_state_*.py`, `packages/forge-core/tests/test_route_delegation_packets.py`, `packages/forge-core/tests/test_help_next_workflow_state.py`
  - Change: map which route files are still required by workflow-state, response contracts, or adapter locale tests
  - Proof: write an explicit ownership table in the PR or a follow-up design note
  - Notes: do not guess here; this slice is where accidental breakage is most likely
  - Execution note: audit grouped `route_delegation_packets.py`, `route_host_capabilities.py`, and `route_lane_plans.py` as clearly live; `route_delegation.py` as maybe live; and `route_preview.py`, `route_preview_builder.py`, `route_preview_output.py`, plus the policy/intent helper chain behind them as likely removable later once route-preview compatibility is retired.

- [x] Step 2: Delete `route_local_companions.py` and remove companion hooks
  - Files: `packages/forge-core/scripts/route_local_companions.py`, `packages/forge-core/scripts/route_preview_builder.py`
  - Change: remove companion inference if no live current-contract path still needs it
  - Proof: targeted route/workflow-state tests fail before change and pass after change
  - Notes: this is the first low-risk cut inside the route cluster
  - Execution note: removed `route_local_companions.py`, deleted `local_companions` from route-preview builder/output payloads, and dropped archival fixture expectations for local companion inference.

- [x] Step 3: Introduce an internal route-compat module boundary
  - Files: affected `packages/forge-core/scripts/route*.py`
  - Change: consolidate the still-live internals behind a smaller compatibility boundary, then delete retired helpers
  - Proof: line-count/file-count reduction plus unchanged targeted workflow-state and adapter tests
  - Notes: success here is fewer modules, not prettier names
  - Execution note: retired the entire route-preview generator stack (`route_preview.py`, builder/output, route policy/intention helpers, smoke fixture pack, and overlay fixture sync), leaving only delegation internals (`route_delegation_packets.py`, `route_host_capabilities.py`, `route_lane_plans.py`) plus workflow-state compatibility readers for historical `route-preview` artifacts.

## Acceptance Criteria

- No generated cache or bytecode directories remain in active `forge-core`.
- Active tests no longer include explicitly archived route-preview coverage files.
- Stale companion/canary references are gone from the active `forge-core/references/` tree.
- `workspace_signals.py` is removed unless a hidden dependency is proven.
- `tooling.md` no longer acts as a duplicate maintainer monolith.
- The route-era cluster is smaller and no longer carries companion-specific dead code.

## Verification

- `python -m pytest packages/forge-core/tests/test_contracts.py -q`
- `python -m pytest packages/forge-core/tests -q`
- `python -m pytest tests/test_operator_surface_registry.py tests/release_repo_test_contracts.py tests/release_repo_test_overlays.py -q`
- `rg -n --glob '!docs/archive/**' --glob '!docs/plans/**' --glob '!dist/**' "companion-skill-contract|companion-routing-smoke-tests|canary-rollout|workspace_signals|route_local_companions" .`
- `git status --short packages/forge-core`

## Risks And Rollback

- Biggest risk: route-era scripts still feed workflow-state and response-contract helpers even though they are no longer public surface.
- Secondary risk: some stale-looking references still support fixture-based tests or compatibility docs and cannot be removed blindly.
- Rollback: restore removed files one slice at a time and rerun the targeted test packet; do not batch-delete the whole route cluster in one change.

## Execution Mode

Recommended execution order:

1. Inline cleanup for cache residue, dead tests, and dead single-file utilities.
2. Separate tranche for stale reference archiving.
3. Dedicated refactor tranche for route-era cluster reduction.

Plan complete and saved to `docs/plans/2026-04-22-forge-core-cleanup-implementation-plan.md`. Choose execution mode:
1. Subagent-Driven - use forge-subagent-driven-development
2. Inline Execution - use forge-executing-plans
