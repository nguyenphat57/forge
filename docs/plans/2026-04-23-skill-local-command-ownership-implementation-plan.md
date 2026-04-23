# Skill-Local Command Ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce the rule that any command used by a Forge sibling skill is sourced inside that skill's package, not `packages/forge-core/commands/`.
**Architecture:** `forge-core/commands/` keeps only core-owned operator/kernel commands. Skill-owned commands live under `packages/forge-skills/<skill>/commands/`; release builds may materialize selected owner commands into bundle `commands/` for backward-compatible runtime entrypoints.
**Tech Stack:** Python 3.13, pytest/unittest, Forge release bundle scripts.

## Source And Current State

- `forge-init` uses `python commands/initialize_workspace.py`, but the source implementation is currently `packages/forge-core/commands/initialize_workspace.py`.
- Other skill-owned commands already live with their owner skills, including customize, session-management, brainstorming, executing-plans, systematic-debugging, using-git-worktrees, and writing-plans.
- Build scripts materialize customize-owned commands into adapter/core bundle `commands/` so global preference restore still works.

## Desired End State

- `packages/forge-skills/init/commands/initialize_workspace.py` is the source command for `forge-init`.
- `packages/forge-core/commands/initialize_workspace.py` does not exist.
- Tests assert that `forge-init` owns its command in place.
- Build and smoke helpers resolve `initialize_workspace.py` from the init skill source.
- Runtime bundle compatibility is preserved by materializing the init command into `dist/<bundle>/commands/initialize_workspace.py`.

## Out Of Scope

- Changing the public `forge-init` workflow semantics.
- Removing top-level materialized bundle commands required by installed host bootstrap docs.
- Reworking unrelated core operator commands such as `resolve_help_next.py`, `run_with_guidance.py`, or `prepare_bump.py`.

## File Structure And Responsibility Map

- `packages/forge-skills/init/commands/initialize_workspace.py`
  - CLI entrypoint for `forge-init` workspace bootstrap.
- `packages/forge-skills/init/commands/_forge_skill_command.py`
  - Source and bundle path bootstrap helper for owner-local skill commands.
- `packages/forge-core/commands/`
  - Core-owned commands only; no `initialize_workspace.py`.
- `packages/forge-core/tests/test_contracts.py`
  - Ownership contract for skill-local commands.
- `packages/forge-core/tests/support.py`
  - Test helper command resolution for init-owned commands.
- `packages/forge-core/tools/smoke_matrix_suites.py`
  - Smoke matrix uses owner command resolution for init.
- `scripts/build_release.py`
  - Materializes init-owned runtime into built bundles for compatibility.
- `docs/architecture/architecture-layers.md`, `docs/current/kernel-tooling.md`
  - Document skill-local command ownership.

## Implementation Tasks

### Task 1: RED the init command ownership contract

- [x] Step 1: Add contract assertions for `forge-init`
  - Files: `packages/forge-core/tests/test_contracts.py`
  - Change: require `packages/forge-skills/init/commands/initialize_workspace.py` and forbid `packages/forge-core/commands/initialize_workspace.py`.
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py::BundleContractTests::test_runtime_commands_are_owned_in_place -q` -> FAIL because the init command still lives in core.

### Task 2: Move the init command to its owner skill

- [x] Step 1: Create owner-local init command files
  - Files: `packages/forge-skills/init/commands/initialize_workspace.py`, `packages/forge-skills/init/commands/_forge_skill_command.py`
  - Change: move the executable source under `forge-init`, keeping the CLI shape unchanged.
  - Proof: `python packages/forge-skills/init/commands/initialize_workspace.py --workspace . --format json` -> PASS.

- [x] Step 2: Remove the core copy
  - Files: `packages/forge-core/commands/initialize_workspace.py`
  - Change: delete the core-owned source copy.
  - Proof: rerun the RED test -> PASS.

### Task 3: Update helper and release resolution

- [x] Step 1: Resolve init commands from the owner skill in tests and smoke tools
  - Files: `packages/forge-core/tests/support.py`, `packages/forge-core/tools/smoke_matrix_suites.py`
  - Change: point source-repo execution at `packages/forge-skills/init/commands/initialize_workspace.py`.
  - Proof: `python -m pytest packages/forge-core/tests/test_initialize_workspace.py -q` -> PASS.

- [x] Step 2: Preserve bundle command compatibility
  - Files: `scripts/build_release.py`, `docs/release/package-matrix.json`
  - Change: materialize init-owned commands into built `commands/` directories where required.
  - Proof: `python scripts/build_release.py --bundle forge-core --force --format json` and path check for `dist/forge-core/commands/initialize_workspace.py` -> PASS.

### Task 4: Update docs and final verification

- [x] Step 1: Update architecture and tooling docs
  - Files: `docs/architecture/architecture-layers.md`, `docs/current/kernel-tooling.md`
  - Change: state that skill-used commands are sourced inside owner skills, even when materialized into runtime bundles.
  - Proof: content check with `rg -n "initialize_workspace.py|skill-owned runtime entrypoints" docs packages/forge-skills/init`.

- [x] Step 2: Run targeted and baseline verification
  - Files: none
  - Change: verify the ownership move.
  - Proof:
    - `python -m pytest packages/forge-core/tests/test_contracts.py::BundleContractTests::test_runtime_commands_are_owned_in_place -q`
    - `python -m pytest packages/forge-core/tests/test_initialize_workspace.py -q`
    - `python scripts/generate_host_artifacts.py --check --format json`
    - `python scripts/verify_repo.py --profile fast`

## Acceptance Criteria

- No active source file `packages/forge-core/commands/initialize_workspace.py` remains.
- `forge-init` owns `commands/initialize_workspace.py` in `packages/forge-skills/init/commands/`.
- Tests fail if a skill-used command is moved back into core.
- Built bundles can still provide the stable top-level command surface when release contracts require it.
- Docs distinguish source ownership from materialized runtime compatibility.

## Verification

- RED: `python -m pytest packages/forge-core/tests/test_contracts.py::BundleContractTests::test_runtime_commands_are_owned_in_place -q`
- Targeted GREEN:
  - `python packages/forge-skills/init/commands/initialize_workspace.py --workspace . --format json`
  - `python -m pytest packages/forge-core/tests/test_contracts.py::BundleContractTests::test_runtime_commands_are_owned_in_place -q`
  - `python -m pytest packages/forge-core/tests/test_initialize_workspace.py -q`
- Broader:
  - `python scripts/generate_host_artifacts.py --check --format json`
  - `python scripts/verify_repo.py --profile fast`

## Risks And Rollback

- Risk: installed bundles expect `commands/initialize_workspace.py` at top level.
  - Rollback: keep source ownership in `forge-init`, but materialize the command into bundle `commands/` during build.
- Risk: path bootstrap differs between source skill bundles and materialized adapter bundles.
  - Rollback: adjust the init command bootstrap to search both source repo and installed sibling layouts.

## Execution Mode

- Chosen mode: Inline Execution.
- Reason: the change is tightly coupled across one source owner move, build materialization, docs, and tests.
