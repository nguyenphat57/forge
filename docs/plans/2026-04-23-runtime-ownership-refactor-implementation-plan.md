# Runtime Ownership Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move owner-specific runtime scripts back to their owning skill or core command package, consolidate only truly shared modules under `packages/forge-core/shared/`, remove `packages/forge-core/engine/`, and keep the public `python commands/...` surface stable.
**Architecture:** Standalone executable commands live under their owner package; shared deterministic support modules live under `forge-core`; repo-root `scripts/` stays repo tooling only.
**Tech Stack:** Python 3.13, unittest/pytest, Forge bundle packaging scripts, generated host artifacts.

## Source And Current State

- The current working tree already contains an in-progress refactor that moved `packages/forge-core/scripts/` into `packages/forge-core/engine/forge_core_runtime/` and introduced `packages/forge-core/commands/` plus skill-local `commands/` wrappers.
- `packages/forge-core/commands/*.py` and `packages/forge-skills/*/commands/*.py` are thin wrappers that forward into `engine/forge_core_runtime/`.
- Build and contract logic now explicitly strip top-level runtime `scripts/` and require `engine/forge_core_runtime/`.
- Baseline evidence before this plan:
  - `python scripts/verify_repo.py --profile fast` -> PASS on 2026-04-23
  - `python -m pytest packages/forge-core/tests/test_contracts.py -q` -> PASS on 2026-04-23

## Desired End State

- `packages/forge-core/shared/` contains shared runtime helpers only.
- `packages/forge-core/commands/` contains real core-owned executable command implementations, not wrappers into `engine/`.
- `packages/forge-skills/<skill>/commands/` contains real skill-owned executable command implementations, not wrappers into `engine/`.
- Any optional skill-local helper modules live with the owning skill package, not in `forge-core`.
- `packages/forge-core/engine/` is deleted.
- Tests, release packaging, generated docs, and install/runtime shims all point to `commands/` and `shared/`, never `engine/`.

## Out Of Scope

- Changing public operator verbs or repo-root `scripts/repo_operator.py` semantics.
- Adding new user-facing features unrelated to runtime ownership cleanup.
- Reorganizing `tools/visual-companion/`.
- Rewriting unrelated docs beyond path/ownership updates required by this refactor.

## File Structure And Responsibility Map

- `packages/forge-core/shared/`
  - Shared runtime support modules reused by core commands, skill commands, tools, and tests.
  - Expected modules: `common.py`, `compat*.py`, `error_translation.py`, `help_next_support.py`, `operator_*`, `preferences*.py`, `prepare_bump_*.py`, `quality_gate_artifacts.py`, `response_contract*.py`, `route_*.py`, `run_guidance_support.py`, `session_state_resolution.py`, `skill_routing.py`, `style_maps.py`, `text_utils.py`, `workflow_*`.
- `packages/forge-core/commands/`
  - Real executable entrypoints for core-owned behaviors: `resolve_help_next.py`, `resolve_preferences.py`, `write_preferences.py`, `run_with_guidance.py`, `session_context.py`, `prepare_bump.py`, `initialize_workspace.py`, `verify_bundle.py`, `verify_bundle_runner.py`, plus retained internal commands such as `bootstrap_workflow_state.py` and `capture_continuity.py` if still required.
- `packages/forge-skills/brainstorming/commands/`
  - Real executable entrypoints for `check_backend_brief.py`, `check_ui_brief.py`, `generate_requirements_checklist.py`, `track_ui_progress.py`.
- `packages/forge-skills/executing-plans/commands/`
  - Real executable entrypoints for `record_direction_state.py`, `record_quality_gate.py`, `record_review_state.py`, `record_stage_state.py`, `track_chain_status.py`, `track_execution_progress.py`.
- `packages/forge-skills/systematic-debugging/commands/`
  - Real executable entrypoint for `translate_error.py`.
- `packages/forge-skills/using-git-worktrees/commands/`
  - Real executable entrypoint for `prepare_worktree.py`.
- `packages/forge-skills/writing-plans/commands/`
  - Real executable entrypoint for `check_spec_packet.py`.
- Repo-root `scripts/`
  - Build, install, verification, and generation tooling only.

## Implementation Tasks

### Task 1: RED the bundle contract for the post-engine topology

- [ ] Step 1: Update the ownership and bundle contract tests to require `shared/` and reject `engine/`
  - Files: `packages/forge-core/tests/test_contracts.py`, `tests/test_release_hardening.py`, `tests/release_repo_test_contracts.py`
  - Change: encode the new topology in tests before moving implementation code
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py -q` -> FAIL because `packages/forge-core/engine/` still exists and `shared/`/real owner implementations are not in place yet
  - Notes: keep the new assertions narrow enough to fail specifically on ownership layout, not on unrelated text churn

- [ ] Step 2: Extend release/install expectations to block shipped `engine/` runtime paths
  - Files: `tests/test_install_bundle_codex_host.py`, `tests/test_install_bundle_antigravity_host.py`, `tests/release_repo_test_install.py`
  - Change: assert bundles include `shared/` and do not include `engine/`
  - Proof: targeted install/release test command(s) -> FAIL for expected missing-path reason before implementation
  - Notes: do not widen into unrelated release assertions

### Task 2: Move shared runtime support into `forge-core/shared/`

- [ ] Step 1: Create the `packages/forge-core/shared/` package and move shared support modules there
  - Files: `packages/forge-core/shared/__init__.py`, moved files from `packages/forge-core/engine/forge_core_runtime/` that remain shared
  - Change: relocate only support modules that are not owned by a specific skill command or core command entrypoint
  - Proof: content check with `rg -n "engine/forge_core_runtime" packages/forge-core/shared packages/forge-core/commands packages/forge-skills` -> output excludes moved support imports from command files
  - Notes: keep import names stable where possible to minimize downstream churn

- [ ] Step 2: Replace `run_engine_command` dispatch with path bootstrap for shared imports only
  - Files: `packages/forge-core/commands/_forge_core_command.py`, `packages/forge-skills/*/commands/_forge_skill_command.py`
  - Change: bootstrap `shared/` and owner command directories on `sys.path` without forwarding execution into a second location
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py -q` -> still FAIL only on not-yet-migrated real command implementations or remaining engine references
  - Notes: helper modules may stay, but they must stop dispatching to `engine/`

### Task 3: Make core-owned commands real implementations

- [ ] Step 1: Move the core command implementations into `packages/forge-core/commands/`
  - Files: `packages/forge-core/commands/*.py` for core-owned commands
  - Change: replace wrapper bodies with the real command implementations and update imports to use `shared/`
  - Proof: `python packages/forge-core/commands/resolve_help_next.py --workspace . --mode help --format json` -> PASS
  - Notes: preserve the public CLI shape exactly

- [ ] Step 2: Update core tools, verification scripts, and test support to import from `shared/` and execute real commands
  - Files: `packages/forge-core/tools/*.py`, `packages/forge-core/tests/support.py`, `scripts/_forge_core_script_proxy.py`, `scripts/verify_repo.py`
  - Change: remove all path assumptions that require `engine/forge_core_runtime`
  - Proof: targeted affected test suites and smoke commands -> PASS
  - Notes: keep repo-root tooling behavior unchanged aside from path resolution

### Task 4: Make skill-owned commands real implementations

- [ ] Step 1: Move brainstorming and writing-plans implementations into their owner packages
  - Files: `packages/forge-skills/brainstorming/commands/*.py`, `packages/forge-skills/writing-plans/commands/check_spec_packet.py`
  - Change: replace wrappers with the real implementations and import shared helpers from `forge-core/shared/`
  - Proof: targeted command runs such as `python packages/forge-skills/brainstorming/commands/check_ui_brief.py --help` -> PASS
  - Notes: keep the behavioral output identical

- [ ] Step 2: Move executing-plans, systematic-debugging, and using-git-worktrees implementations into their owner packages
  - Files: `packages/forge-skills/executing-plans/commands/*.py`, `packages/forge-skills/systematic-debugging/commands/translate_error.py`, `packages/forge-skills/using-git-worktrees/commands/prepare_worktree.py`
  - Change: replace wrappers with the real implementations and update any internal imports
  - Proof: owner command smoke checks plus the matching targeted tests -> PASS
  - Notes: preserve existing file names so generated docs do not need contract changes beyond path ownership wording

### Task 5: Remove `engine/` references from packaging, docs, and generated artifacts

- [ ] Step 1: Update package matrices, registries, build/install tooling, and docs to reference `shared/` plus owner `commands/`
  - Files: `docs/release/package-matrix.json`, `packages/forge-core/data/orchestrator-registry.json`, `scripts/build_release.py`, `scripts/operator_surface_support.py`, generated-host-artifact sources, current docs, overlay docs, install tests
  - Change: stop mentioning `engine/forge_core_runtime`; describe `shared/` as implementation detail and `commands/` as executable surface
  - Proof: `python scripts/generate_host_artifacts.py --check --format json` and `python scripts/generate_overlay_skills.py --check --format json` -> FAIL before regeneration if any source/output drift exists, then PASS after regeneration
  - Notes: preserve public wording where only the path is changing

- [ ] Step 2: Delete the now-unused `packages/forge-core/engine/` tree
  - Files: `packages/forge-core/engine/`
  - Change: remove the directory after all imports, manifests, and tests no longer depend on it
  - Proof: `rg -n "engine/forge_core_runtime|packages/forge-core/engine" packages scripts tests docs` -> no matches outside archival/history artifacts explicitly allowed by current contracts
  - Notes: if any remaining reference is intentional historical text, document it and update the relevant contract accordingly

### Task 6: GREEN the full verification stack

- [ ] Step 1: Rerun the targeted RED suites and command smokes
  - Files: none
  - Change: verify the topology and owner commands are now green
  - Proof:
    - `python -m pytest packages/forge-core/tests/test_contracts.py -q`
    - targeted install/release tests updated in Tasks 1 and 5
    - representative command smokes for core and skill-owned commands
  - Notes: rerun the exact RED proof first before broader checks

- [ ] Step 2: Run the broader baseline
  - Files: none
  - Change: verify repo-wide integrity after the refactor
  - Proof:
    - `python scripts/generate_host_artifacts.py --check --format json`
    - `python scripts/generate_overlay_skills.py --check --format json`
    - `python scripts/verify_repo.py --profile fast`
    - `python scripts/verify_repo.py`
  - Notes: if the full repo verification is too slow or blocked, record the blocker explicitly and do not claim full completion

## Acceptance Criteria

- No active bundle, script, tool, or test depends on `packages/forge-core/engine/`.
- Core commands execute their own code directly from `packages/forge-core/commands/`.
- Skill commands execute their own code directly from `packages/forge-skills/<skill>/commands/`.
- Shared runtime helpers are centralized under `packages/forge-core/shared/`.
- Build/install/release outputs ship `shared/` and `commands/`, not `engine/`.
- Generated docs and operator surfaces consistently describe the new layout.

## Verification

- Baseline before editing:
  - `python scripts/verify_repo.py --profile fast`
  - `python -m pytest packages/forge-core/tests/test_contracts.py -q`
- RED/targeted verification during implementation:
  - `python -m pytest packages/forge-core/tests/test_contracts.py -q`
  - targeted install/release suites updated by Task 1
  - representative direct command invocations for moved owner commands
- Final verification:
  - `python scripts/generate_host_artifacts.py --check --format json`
  - `python scripts/generate_overlay_skills.py --check --format json`
  - `python scripts/verify_repo.py --profile fast`
  - `python scripts/verify_repo.py`

## Risks And Rollback

- Risk: import bootstrapping for directly executed command scripts may break on installed bundles if path setup is incomplete.
  - Rollback: restore the previous wrapper behavior for the affected command only while preserving the new ownership map, then continue migration in a smaller slice.
- Risk: generated artifact sources may drift from overlay outputs after path renames.
  - Rollback: regenerate from source-of-truth files and rerun the host artifact checks before proceeding.
- Risk: existing dirty changes may overlap with the same files.
  - Rollback: integrate incrementally, do not revert unrelated edits, and isolate unexpected conflicts before continuing.

## Execution Mode

- Chosen mode: `Subagent-Driven`
- Controller responsibilities:
  - lock the `shared/` bootstrap shape and command ownership map
  - integrate cross-cutting packaging/docs/test changes
  - run final verification and claim boundary checks
- Candidate worker packets:
  - core shared/bootstrap lane
  - skill-owned command migration lane
  - packaging/docs/install verification lane
