# Independent Sibling Skill Bundles Implementation Plan

Status: historical implemented migration slice

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every shipped Forge sibling skill bundle self-contained for its own guidance assets so agents never need to resolve skill-local references by falling back into the orchestrator bundle.
**Architecture:** Use `packages/forge-skills/` as the canonical source for sibling skills while keeping each skill's referenced markdown companions inside that skill's own source tree and teaching release/install manifests to declare those bundled files explicitly.
**Tech Stack:** Python release scripts, markdown skill/reference files, pytest/unittest contract suite.

## Source And Current State

- `scripts/build_release.py` currently builds sibling skills by copying the source directory and writing a manifest with `required_bundle_paths` hard-coded to only `BUILD-MANIFEST.json` and `SKILL.md`.
- Shipped sibling skills in `packages/forge-skills/` must carry their own `references/` trees when their `SKILL.md` asks the agent to load markdown companions.
- At least these canonical sibling skills reference markdown files outside their own source directories:
  - `packages/forge-skills/brainstorming/SKILL.md`
  - `packages/forge-skills/systematic-debugging/SKILL.md`
  - `packages/forge-skills/subagent-driven-development/SKILL.md`
- Several skills still state that shared scripts and references live in the installed orchestrator bundle, which conflicts with the desired self-contained bundle model.
- `skills/forge-customize/` already demonstrates the desired pattern: `SKILL.md` plus colocated `references/` files inside one public skill directory.

## Desired End State

- Every shipped Forge sibling skill is self-contained for every markdown reference it asks the agent to read.
- Every shipped sibling skill manifest lists the copied skill-local reference files under `packaging.required_bundle_paths`.
- Release bundles under `dist/forge-*` and installed sibling skills under host homes preserve those bundled reference files.
- Sibling skill wording no longer tells the agent to rely on orchestrator-bundle fallback for references.

## Out Of Scope

- Duplicating shared runtime scripts, locale data, or adapter host assets into sibling skills.
- Changing `forge-codex` or `forge-antigravity` overlay packaging beyond fallout required to install the updated sibling skills.
- Reworking the overall split-skill architecture or bundle naming.

## File Structure And Responsibility Map

- `packages/forge-skills/<skill>/`
  - `SKILL.md`: canonical public workflow instructions for that skill.
  - `references/**`: skill-local markdown companions required by `SKILL.md`.
- `scripts/build_release.py`
  - sibling skill bundle build and manifest generation.
- `tests/`
  - release and install contract coverage for `dist/` bundles and host installs.
- `packages/forge-core/tests/test_contracts.py`
  - canonical source-tree contract coverage for skill-local references and wording.

## Implementation Tasks

### Task 1: Lock the new sibling skill bundle contract with RED

- [ ] Step 1: Add source-tree contract coverage for skill-local references
  - Files: `packages/forge-core/tests/test_contracts.py`
  - Change: assert every reference path mentioned in a sibling skill resolves inside that skill directory and assert the old orchestrator-bundle reference fallback wording is gone for affected skills
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py -q` -> FAIL for the expected missing reference / stale wording reasons
  - Notes: keep the assertions scoped to sibling skill self-containment

- [ ] Step 2: Add release/install contract coverage for bundled sibling references
  - Files: `tests/release_repo_test_contracts.py`, `tests/test_install_bundle_design.py`, `tests/test_install_bundle_codex_host.py`, `tests/test_install_bundle_antigravity_host.py`
  - Change: assert sibling skill manifests enumerate bundled reference files and installed sibling skills keep those files on disk
  - Proof: targeted pytest command fails before implementation because manifests and installed skill directories do not yet include those references
  - Notes: keep `scripts/` and `data/` absent from sibling skills unless a skill explicitly needs them

### Task 2: Make canonical sibling skill sources self-contained

- [ ] Step 1: Copy required markdown references into the owning skill directories
  - Files: `packages/forge-skills/brainstorming/references/**`, `packages/forge-skills/systematic-debugging/references/**`, `packages/forge-skills/subagent-driven-development/references/**`
  - Change: colocate every markdown companion each skill asks the agent to load
  - Proof: rerun the source-tree contract test and confirm the reference-resolution assertions pass
  - Notes: copy from canonical active references, not archive or dist outputs

- [ ] Step 2: Remove stale shared-bundle dependency wording from sibling skills
  - Files: `packages/forge-skills/brainstorming/SKILL.md`, `packages/forge-skills/systematic-debugging/SKILL.md`, `packages/forge-skills/writing-plans/SKILL.md`, `packages/forge-skills/executing-plans/SKILL.md`, `packages/forge-skills/test-driven-development/SKILL.md`
  - Change: delete or rewrite lines that tell the agent skill references live in the orchestrator bundle
  - Proof: rerun the source-tree contract test and confirm the stale-wording assertions pass
  - Notes: if a skill truly still depends on shared runtime scripts, keep that distinction explicit without implying markdown reference fallback

### Task 3: Teach release/install manifests the expanded sibling bundle closure

- [ ] Step 1: Compute sibling `required_bundle_paths` from actual bundled files
  - Files: `scripts/build_release.py`
  - Change: replace the hard-coded two-file sibling manifest contract with a deterministic list that includes `SKILL.md`, `BUILD-MANIFEST.json`, and any copied skill-local files
  - Proof: rerun the targeted release/install test command and confirm the manifest assertions turn green
  - Notes: keep ordering stable so fingerprints and tests stay deterministic

- [ ] Step 2: Rebuild release outputs and verify host installs preserve self-contained sibling skills
  - Files: `dist/**` generated by build, installed temp homes exercised by tests
  - Change: ensure `build_release.build_all()` and install flows copy the expanded sibling skill directories without regressions
  - Proof: targeted release/install test command passes
  - Notes: no manual edits under `dist/`

## Acceptance Criteria

- Every markdown reference mentioned in a shipped Forge sibling `SKILL.md` exists under that skill's own source directory.
- Generated sibling skill manifests list those bundled references explicitly.
- `dist/forge-*` sibling bundles and host-installed sibling skills keep the same reference files.
- No shipped sibling skill claims that markdown references must be loaded from the orchestrator bundle.

## Verification

- `python -m pytest packages/forge-core/tests/test_contracts.py -q`
- `python -m pytest tests/release_repo_test_contracts.py tests/test_install_bundle_design.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q`
- `python scripts/build_release.py --format json`

## Risks And Rollback

- Biggest risk: over-bundling shared runtime assets into sibling skills and accidentally bloating or duplicating executable support files.
- Secondary risk: stale copied references drifting from the canonical active references if the copy/update path is not disciplined.
- Rollback: revert the sibling-skill reference directories and manifest-generation change together, then rerun the same verification packet; do not keep half-migrated skill-local references.

## Execution Mode

Recommended execution order:

1. Inline RED on source and release/install contract tests.
2. Inline source-tree bundling of skill-local references and wording cleanup.
3. Inline build-manifest update and targeted verification.

Plan complete and saved to `docs/plans/2026-04-22-independent-sibling-skill-bundles-implementation-plan.md`. Choose execution mode:
1. Subagent-Driven - use forge-subagent-driven-development
2. Inline Execution - use forge-executing-plans
