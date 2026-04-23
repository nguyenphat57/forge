# Remove Repo-Local Install Backups Implementation Plan

Status: implemented

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the repo-root `.install-backups/` contract so Forge stays repo-first while preserving an explicit, non-repo-local rollback snapshot path for runtime installs.
**Architecture:** Replace the default backup root derived from `ROOT_DIR` with a runtime-managed backup root derived from the install target and host state layout, keep `--backup-dir` as an explicit override, and update docs/tests so the source repo no longer treats `.install-backups/` as normal active residue.
**Tech Stack:** Python install/runtime scripts, markdown docs, unittest/pytest contract coverage.

## Source And Current State

- `scripts/install_bundle_paths.py` hard-codes `DEFAULT_BACKUP_DIR = ROOT_DIR / ".install-backups"`.
- `scripts/install_bundle_runtime.py` resolves `backup_root` from `DEFAULT_BACKUP_DIR` unless `--backup-dir` is passed.
- `scripts/install_bundle_host.py` reuses that backup root for host-activation snapshots such as `AGENTS.md` and `GEMINI.md`.
- Current maintainer docs still advertise `.install-backups/` as the default install safety path:
  - `README.md`
  - `docs/release/install.md`
- Repo hygiene code also treats `.install-backups/` as an expected repo-local residue:
  - `scripts/scan_repo_secrets.py`
  - `packages/forge-core/tests/test_contracts.py`
- Most install tests pass an explicit temp `backup_dir`, so the default backup-root behavior is only weakly specified today.

## Desired End State

- Default installs no longer create or depend on a repo-local `.install-backups/` directory.
- Default backup snapshots resolve outside the source repo under runtime-managed state:
  - canonical Codex installs: under `CODEX_HOME/forge-codex/...`
  - canonical Gemini installs: under `GEMINI_HOME/antigravity/forge-antigravity/...`
  - non-canonical explicit targets: under that target's derived adapter state root
- Backup behavior remains available by default unless the operator passes `--no-backup`.
- `--backup-dir` remains supported as an explicit override for tests or one-off operator flows.
- Install reports and manifests still expose the resolved backup path when a snapshot is actually planned.
- Current docs and repo hygiene contracts no longer normalize `.install-backups/` as an active repo artifact.

## Out Of Scope

- Removing install backups entirely from the product.
- Redesigning the rollback operator, release rollback strategy, or rollout ledgers.
- Changing bundle fingerprints or release packaging beyond fallout required by the new backup-root contract.
- Auto-deleting a user's historical `.install-backups/` tree from an already-used repo checkout.
- Renaming public JSON fields such as `backup_path` unless the implementation proves that schema churn is unavoidable.

## File Structure And Responsibility Map

- `scripts/install_bundle_paths.py`
  - canonical path resolution for install targets, state roots, and the new default backup root.
- `scripts/install_bundle_runtime.py`
  - install planning and execution, including planned backup paths for bundle sync.
- `scripts/install_bundle_host.py`
  - host activation planning and host-file snapshot paths built on the resolved backup root.
- `scripts/install_bundle.py`
  - CLI surface and option wording.
- `scripts/install_bundle_report.py`
  - user-facing text and manifest fields that expose backup planning.
- `scripts/scan_repo_secrets.py`
  - repo-local residue ignore list.
- `README.md`, `docs/release/install.md`, `docs/current/install-and-activation.md`
  - maintainer-facing install contract docs.
- `tests/release_repo_test_install.py`
  - install runtime contract coverage for default and explicit backup paths.
- `tests/test_install_bundle_codex_host.py`, `tests/test_install_bundle_antigravity_host.py`
  - host activation backup path coverage.
- `tests/test_release_acceleration.py`, `tests/test_runtime_tool_registration.py`
  - acceleration and installed-runtime regression coverage that should stay compatible with the new default.
- `packages/forge-core/tests/test_contracts.py`
  - repo hygiene rules that should stop special-casing `.install-backups/` as normal active tree residue.

## Implementation Tasks

### Task 1: Lock the repo-first backup contract with RED

- [ ] Step 1: Add tests for the new default backup-root resolution
  - Files: `tests/release_repo_test_install.py`, `tests/test_install_bundle_codex_host.py`, `tests/test_install_bundle_antigravity_host.py`
  - Change: assert that installs without `backup_dir=` plan backup paths outside `ROOT_DIR`, and for canonical host installs assert the path resolves under the host-managed Forge state root instead of `.install-backups/`
  - Proof: `python -m pytest tests/release_repo_test_install.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q` -> FAIL because current planning still resolves backup paths under the repo root
  - Notes: cover both bundle backup paths and host-activation backup paths

- [ ] Step 2: Add repo-hygiene and docs contract checks for removing `.install-backups/` from the active story
  - Files: `packages/forge-core/tests/test_contracts.py`
  - Change: stop exempting `.install-backups/` from active-tree hygiene scans and add assertions that current install docs no longer advertise that repo-local path
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py -q` -> FAIL because current source still references `.install-backups/`
  - Notes: keep `docs/archive/**`, `docs/audits/**`, and `docs/plans/**` outside the active-current contract unless a current doc is intentionally being tested

### Task 2: Move default backup resolution out of the repo tree

- [ ] Step 1: Introduce a runtime-managed default backup-root helper
  - Files: `scripts/install_bundle_paths.py`
  - Change: replace `DEFAULT_BACKUP_DIR = ROOT_DIR / ".install-backups"` with a helper that derives the default backup root from the install target's state root, for example `<state-root>/rollbacks/install`, while keeping explicit `--backup-dir` support intact
  - Proof: rerun `python -m pytest tests/release_repo_test_install.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q`
  - Notes: canonical host installs should land under canonical host state; explicit custom targets should fall back to `resolve_adapter_state_root(target_path)`

- [ ] Step 2: Rewire install planning and host activation to consume the new helper
  - Files: `scripts/install_bundle_runtime.py`, `scripts/install_bundle_host.py`
  - Change: plan both bundle-sync backups and host-activation backups from the resolved non-repo backup root, without changing the existing skip-sync semantics when the target already matches the source
  - Proof: rerun the exact targeted test command and confirm the previous RED turns GREEN
  - Notes: preserve `backup_enabled`, `backup_path`, and host activation report fields unless a failing contract forces a schema edit

- [ ] Step 3: Keep CLI/report behavior coherent after the path move
  - Files: `scripts/install_bundle.py`, `scripts/install_bundle_report.py`
  - Change: update help text and human-readable report wording so it no longer implies repo-local backups while still explaining `--backup-dir` and `--no-backup`
  - Proof: `python scripts/install_bundle.py forge-codex --dry-run --format json` and `python scripts/install_bundle.py forge-antigravity --dry-run --format json` both succeed and expose non-repo default backup planning when sync is required
  - Notes: do not start real host mutation in this step; dry-run is enough for wording and report-shape verification

### Task 3: Remove `.install-backups/` from the current repo story

- [ ] Step 1: Update maintainer docs to the new repo-first backup contract
  - Files: `README.md`, `docs/release/install.md`, `docs/current/install-and-activation.md`
  - Change: replace `.install-backups/` guidance with runtime-managed backup-root guidance and keep `--backup-dir` documented as an explicit override
  - Proof: `python -m pytest packages/forge-core/tests/test_contracts.py -q` and `rg -n "\.install-backups" README.md docs/current docs/release scripts packages tests`
  - Notes: current docs should stop normalizing repo-local install residue; historical docs can remain historical

- [ ] Step 2: Remove repo tooling exemptions that only existed for `.install-backups/`
  - Files: `scripts/scan_repo_secrets.py`, `packages/forge-core/tests/test_contracts.py`
  - Change: drop `.install-backups` from active ignore/exemption lists that were only needed because the installer wrote inside the repo
  - Proof: rerun `python -m pytest packages/forge-core/tests/test_contracts.py -q`
  - Notes: keep `.git`, `dist`, caches, and other real generated directories unchanged unless this tranche touches them directly

- [ ] Step 3: Run the release/install regression baseline
  - Files: none
  - Change: verify the new default backup-root contract does not break bundle build, install dry-run, or runtime registration expectations
  - Proof: `python -m pytest tests/release_repo_test_install.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py tests/test_release_acceleration.py tests/test_runtime_tool_registration.py packages/forge-core/tests/test_contracts.py -q`
  - Notes: if this baseline is too narrow after implementation, widen it instead of swapping to a weaker command

## Acceptance Criteria

- Running install planning without `--backup-dir` no longer points at `ROOT_DIR/.install-backups`.
- Canonical Codex and Gemini installs resolve default backup paths under their host-managed Forge state roots.
- Explicit custom targets resolve default backup paths under the derived adapter state root for that target, not the source repo.
- Current maintainer docs no longer tell operators that `.install-backups/` is the default install safety location.
- Repo hygiene code and tests no longer special-case `.install-backups/` as expected current-tree residue.
- Existing install manifests and reports still expose usable backup-path information when backups are enabled.

## Verification

- `python -m pytest tests/release_repo_test_install.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q`
- `python -m pytest tests/test_release_acceleration.py tests/test_runtime_tool_registration.py -q`
- `python -m pytest packages/forge-core/tests/test_contracts.py -q`
- `python scripts/install_bundle.py forge-codex --dry-run --format json`
- `python scripts/install_bundle.py forge-antigravity --dry-run --format json`
- `rg -n "\.install-backups" README.md docs/current docs/release scripts packages tests`

## Risks And Rollback

- Biggest risk: moving the default backup root into state layout could accidentally place rollback snapshots somewhere unstable or surprising for explicit custom targets.
- Secondary risk: host-activation backup paths could diverge from bundle backup paths if the new helper is not used consistently.
- Documentation risk: current docs might stop mentioning `.install-backups/` while tests or CLI help still imply that path, leaving an inconsistent operator story.
- Rollback: revert the backup-root helper and every dependent doc/test update together, then rerun the same verification packet; do not keep a half-migrated contract where code and docs disagree about backup location.

## Execution Mode

Recommended execution order:

1. Inline RED on install-path and repo-hygiene tests.
2. Inline path-resolution and install-planning implementation.
3. Inline doc and repo-tooling cleanup.
4. Inline targeted regression baseline.

Plan complete and saved to `docs/plans/2026-04-23-remove-install-backups-repo-first-implementation-plan.md`. Choose execution mode:
1. Subagent-Driven - use forge-subagent-driven-development
2. Inline Execution - use forge-executing-plans
