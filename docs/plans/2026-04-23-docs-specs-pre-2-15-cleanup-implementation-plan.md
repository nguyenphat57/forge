# Docs Specs Pre-2.15 Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

Status: implemented

**Goal:** Remove live historical docs/specs that predate the Forge `2.15.0` stable line so current maintainers use current docs and git history instead of archive sidecars.
**Architecture:** Keep source-of-truth docs needed by build, install, and generated artifacts; delete historical docs/specs/plans/audits/release notes that are no longer a live reference surface.
**Tech Stack:** Markdown docs, JSON release metadata, Python unittest/pytest contracts.

## Source And Current State

- `docs/archive/**`, `docs/audits/**`, `docs/legacy/**`, `docs/specs/**`, and `docs/plans/**` contain historical plans, specs, audits, and archived references predating `2.15.0`.
- Release docs still include `1.10.x` release-note/checklist files and public readiness text that points to historical reports.
- Tests currently assert an archive boundary and specific historical plan files.

## Desired End State

- Live docs keep only current architecture, current maintainer docs, current release/install process, generated host artifact sources, and this cleanup plan.
- Pre-`2.15.0` historical docs/specs are removed from the live tree and recoverable from git history only.
- Tests assert that the pre-`2.15.0` docs/specs surface is pruned rather than archived.

## Out Of Scope

- Do not remove package source, runtime code, current generated-host artifact sources, or release package matrix metadata.
- Do not remove generic skill template references such as `docs/specs/YYYY-MM-DD-...`.
- Do not scrub every historical version mention from changelog or `.brain`; only remove live docs/specs references that depend on deleted files.

## File Structure And Responsibility Map

- `docs/archive/`, `docs/audits/`, `docs/legacy/`, `docs/specs/`: delete entirely.
- `docs/plans/`: delete all older plan/spec review files; keep only this implementation plan.
- `docs/release/`: delete pre-`2.15.0` release-note/checklist files; keep current process/install/readiness/package matrix.
- `docs/current/architecture.md`, `docs/release/public-readiness.md`, `docs/release/release-process.md`: remove archive-era wording.
- `tests/test_release_hardening.py`, `tests/test_operator_surface_registry.py`, `packages/forge-core/tests/test_contracts.py`: update contracts from archive-retention to prune-current-live-history.

## Implementation Tasks

### Task 1: Contract RED

- [x] Step 1: Update tests to require pre-`2.15.0` docs/specs cleanup.
  - Files: `tests/test_release_hardening.py`, `tests/test_operator_surface_registry.py`, `packages/forge-core/tests/test_contracts.py`
  - Change: assert removed archive/audit/legacy/spec/release-note paths and allow only current cleanup plan under `docs/plans/`.
  - Proof: targeted pytest should fail while historical docs remain.

### Task 2: Remove Historical Docs

- [x] Step 1: Delete historical docs/specs/plans/audits and stale release-note files.
  - Files: `docs/archive/**`, `docs/audits/**`, `docs/legacy/**`, `docs/specs/**`, stale `docs/plans/**`, stale `docs/release/1.10*`, stale `docs/release/github-public-switch-checklist.md`
  - Proof: targeted pytest should pass after deletion and docs wording updates.

### Task 3: Current Docs Alignment

- [x] Step 1: Update current docs that still advertise archive-era references.
  - Files: `docs/current/architecture.md`, `docs/release/public-readiness.md`, `docs/release/release-process.md`
  - Proof: `rg "docs/archive|docs/audits|github-public-switch-checklist|1.10.1|real-repo canary" docs/current docs/release tests packages/forge-core/tests -n` has no live current/reference requirement hits.

### Task 4: Verification

- [x] Step 1: Run targeted tests.
  - Files: none
  - Proof: `python -m pytest tests/test_release_hardening.py tests/test_operator_surface_registry.py packages/forge-core/tests/test_contracts.py -q`

- [x] Step 2: Run full repo verification.
  - Files: none
  - Proof: `python scripts/verify_repo.py`

## Acceptance Criteria

- Historical docs/specs before `2.15.0` are not live tracked docs.
- Current docs do not tell maintainers to use archived roadmap/spec material.
- Public readiness no longer references removed historical evidence/checklists.
- Repo verification passes.

## Verification

- `python -m pytest tests/test_release_hardening.py tests/test_operator_surface_registry.py packages/forge-core/tests/test_contracts.py -q`
- `python scripts/verify_repo.py`

## Risks And Rollback

- Risk: deleting docs that tests still treat as contract can expose hidden references. Mitigation: update contract tests first and run full verification.
- Rollback: restore deleted docs from git history if a future release needs archaeology, but do not keep them as live current references.

## Execution Mode

Inline execution in this session using forge-executing-plans.
