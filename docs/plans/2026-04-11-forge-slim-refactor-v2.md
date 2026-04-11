Date: 2026-04-11
Status: current roadmap

# Forge Slim Refactor v2

## Summary

This roadmap reopens Forge explicitly after the `1.15.x` closure line.
The goal is to reduce cognitive load and maintenance surface without changing the release contract, bundle fingerprinting, install safety, or runtime-tool boundaries.

The tranche stays docs-first:

- create one current docs spine under `docs/current/`
- archive historical plans and specs out of the active reading path
- collapse the source-repo operator surface to `scripts/repo_operator.py`
- keep Codex output paths stable while deduplicating wrapper source and generator logic
- keep `verify_repo.py` as the canonical release gate

## Phases

### Phase 1: Current docs spine and archive

- Create:
  - `docs/current/architecture.md`
  - `docs/current/operator-surface.md`
  - `docs/current/install-and-activation.md`
- Move historical roadmap material to `docs/archive/plans/`.
- Move historical spec material to `docs/archive/specs/`.
- Publish `docs/archive/INDEX.md` so archived material stays discoverable.
- Keep `docs/plans/2026-04-02-forge-1.15.x-maintenance-closure.md` only as historical closure evidence.

Checkpoint A:
- docs/reference tests stay green
- source-repo command surface is not changed yet

### Phase 2: Source-repo operator dispatcher

- Add `scripts/repo_operator.py` as the only public source-repo operator entrypoint.
- Route:
  - `resume`, `save`, `handover` -> `session_context.py`
  - `help`, `next` -> `resolve_help_next.py`
  - `run` -> `run_with_guidance.py`
  - `bump` -> `prepare_bump.py`
  - `rollback` -> `resolve_rollback.py`
  - `customize` -> `resolve_preferences.py` or `write_preferences.py`
  - `init` -> `initialize_workspace.py`
  - `capture-continuity` -> `capture_continuity.py`
- Update `AGENTS.md`, current docs, and source-repo tests to the dispatcher contract.

Checkpoint B:
- dispatcher tests pass
- machine-readable operator metadata points at `repo_operator.py`
- old proxy file names are no longer documented

### Phase 3: Codex wrapper source rationalization

- Keep installed/output paths stable:
  - `operator/help.md`
  - `operator/next.md`
  - `operator/run.md`
  - `operator/bump.md`
  - `operator/rollback.md`
  - `operator/customize.md`
  - `operator/init.md`
- Replace seven separate canonical Codex wrapper sources with one shared template plus action context.
- Use `operator_surface.actions` registry metadata as machine-readable input and render action-specific prose through the shared generator path.
- Leave Antigravity runtime layout unchanged; only update wording when needed to stay aligned with current docs.

Checkpoint C:
- generated host artifacts are fresh
- Codex wrapper outputs still exist at the same paths
- shared source generation is covered by tests

### Phase 4: Cleanup and rollout sync

- Remove the nine repo-root proxy scripts after dispatcher adoption is complete.
- Keep source-repo changes and installed-runtime sync rules distinct:
  - repo-local `AGENTS.md` changes apply immediately in the source repo
  - global template or installed bundle changes require rebuild and re-activation
- Keep `install_bundle_host.py` behavior intact in this tranche; defer deeper activation refactor to a later roadmap slice.

Checkpoint D:
- source repo only documents `repo_operator.py`
- proxy files are removed
- full verification is green

## Public interface changes

- Source-repo operator surface changes from many repo-root scripts to:
  - `python scripts/repo_operator.py <action> ...`
- Current maintainer docs move to:
  - `docs/current/*`
- Historical plans and specs leave the active reading path and move under:
  - `docs/archive/*`

## Non-goals

- No change to `install_bundle.py` CLI.
- No change to `--activate-codex` or `--activate-gemini`.
- No change to bundle fingerprints, manifests, or adapter state layout.
- No deep `install_bundle_host.py` rewrite in this tranche.
- No runtime wrapper path changes for installed Codex operator files.

## Verification plan

- targeted docs/reference suites after Phase 1
- dispatcher and source-repo contract tests after Phase 2
- host-artifact generation and overlay tests after Phase 3
- `python scripts/verify_repo.py --profile fast`
- `python scripts/verify_repo.py --format json`

## Decision guardrails

- This is a roadmap-level refactor, not a maintenance-only drift fix.
- Docs-first does not mean docs-only; every docs move must keep the repo in a consistent, testable state.
- The breaking change is the source-repo entrypoint consolidation, not the installed runtime contract.
- Codex is the main slimming target because it carries the heaviest generated wrapper surface.
