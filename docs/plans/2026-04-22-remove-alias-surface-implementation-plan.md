# Remove Alias Surface Implementation Plan

Status: implemented

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove slash-based compatibility/operator alias surface from the current Forge contract so host guidance points users to natural language and discoverable Forge skills instead of alias wrappers.
**Architecture:** Keep `repo_operator.py` and host-native skill discovery as the canonical surfaces; trim alias metadata, generated bootstrap wording, and tests that currently preserve alias visibility.
**Tech Stack:** Python, Markdown, generated host artifacts, pytest/unittest

## Source And Current State

- Forge currently treats natural language and sibling skills as canonical, but generated host artifacts and overlay references still publish slash aliases.
- The repo contains tests, registry metadata, and generated host artifact sources that keep those aliases visible.
- `build_release.py` and host-artifact generation already provide a deterministic way to regenerate affected bundle outputs after source edits.

## Desired End State

- Host bootstrap docs and operator-surface references no longer list slash aliases.
- Registry metadata no longer carries primary or compatibility slash aliases for host operator actions.
- Current docs describe operator actions through natural-language examples and canonical repo operator entrypoints only.
- Release and overlay tests assert the alias-free contract.

## Out Of Scope

- Changing the underlying `repo_operator.py` action set.
- Removing session natural-language examples such as `save context` or `handover`.
- Reworking subagent support itself beyond removing `/delegate` alias wording.

## File Structure And Responsibility Map

- `docs/plans/2026-04-22-remove-alias-surface-implementation-plan.md`: execution plan and proof path for this slice.
- `tests/test_operator_surface_registry.py`: contract tests for current registry/docs posture.
- `tests/release_repo_test_overlays.py`: overlay and dist assertions for generated host artifacts and bundle contents.
- `tests/release_repo_test_contracts.py`: release-contract assertions for generated outputs and required bundle paths.
- `packages/forge-core/data/orchestrator-registry.json`: host/repo operator metadata that currently carries alias fields.
- `docs/current/operator-surface.md`: maintainer-facing current operator contract.
- `docs/architecture/generated-host-artifacts/AGENTS.global.canonical.md`: canonical Codex global bootstrap wording.
- `docs/architecture/generated-host-artifacts/GEMINI.global.canonical.md`: canonical Antigravity global bootstrap wording.
- `docs/architecture/generated-host-artifacts/codex/references/codex-operator-surface.md`: canonical Codex operator surface reference.
- `packages/forge-codex/overlay/*` and `packages/forge-antigravity/overlay/*`: generated outputs refreshed from canonical sources.

## Implementation Tasks

### Task 1: Lock RED on alias-free contract

- [ ] Step 1: Update targeted tests so the expected contract removes slash alias wording and alias metadata
  - Files: `tests/test_operator_surface_registry.py`, `tests/release_repo_test_overlays.py`, `tests/release_repo_test_contracts.py`
  - Change: replace assertions that preserve `/delegate`, `/customize`, `/init`, alias headings, and alias-required bundle outputs with alias-free expectations
  - Proof: `python -m pytest tests/test_operator_surface_registry.py tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py -q` -> FAIL for the expected stale alias content
  - Notes: keep scope limited to published alias surface, not unrelated bundle structure

### Task 2: Remove alias metadata and canonical wording

- [ ] Step 2: Edit registry and canonical source docs to remove slash alias publication
  - Files: `packages/forge-core/data/orchestrator-registry.json`, `docs/current/operator-surface.md`, `docs/architecture/generated-host-artifacts/AGENTS.global.canonical.md`, `docs/architecture/generated-host-artifacts/GEMINI.global.canonical.md`, `docs/architecture/generated-host-artifacts/codex/references/codex-operator-surface.md`
  - Change: drop slash alias sections and `/delegate` compatibility wording; keep natural-language guidance and canonical action names
  - Proof: rerun the exact targeted command first
  - Notes: do not change the actual operator action names or session natural-language examples

- [ ] Step 3: Regenerate host artifacts and bundled outputs
  - Files: generated outputs under `packages/forge-codex/overlay/`, `packages/forge-antigravity/overlay/`, `docs/current/`, and `dist/`
  - Change: run the canonical generator/build flow so generated markdown and manifests match the alias-free sources
  - Proof: rerun the exact targeted command first
  - Notes: use the repo’s existing generation/build commands rather than hand-editing generated files

### Task 3: Prove the updated contract

- [ ] Step 4: Run the targeted alias-surface test set after regeneration
  - Files: none
  - Change: verify GREEN on the same tests used for RED
  - Proof: `python -m pytest tests/test_operator_surface_registry.py tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py -q`
  - Notes: this must pass before any broader claim

- [ ] Step 5: Run a broader generated-artifact baseline
  - Files: none
  - Change: confirm host artifact generation and install-host contracts still hold after alias removal
  - Proof: `python -m pytest tests/test_host_artifact_generation.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q`
  - Notes: record residual risk if any generated bundle path intentionally changes and requires follow-up

## Acceptance Criteria

- No current bootstrap or operator-surface doc publishes slash alias lists.
- Registry metadata for host operator actions no longer exposes slash aliases.
- Generated Codex and Antigravity host artifacts are refreshed and consistent with the alias-free contract.
- The targeted and broader verification commands pass.

## Verification

- RED: `python -m pytest tests/test_operator_surface_registry.py tests/release_repo_test_overlays.py tests/release_repo_test_contracts.py -q`
- GREEN: same command after implementation
- Baseline: `python -m pytest tests/test_host_artifact_generation.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q`

## Risks And Rollback

- Risk: generated bundle path expectations may still require thin operator workflow files even if the docs stop publishing slash aliases.
- Risk: removing alias metadata from the registry could affect tests or generators that assume the fields exist.
- Rollback: revert the alias-removal edits and regenerate host artifacts to restore previous published surfaces.

## Execution Mode

- Inline execution via `forge-executing-plans`
