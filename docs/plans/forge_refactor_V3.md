Date: 2026-04-11
Status: historical implemented contraction tranche

# Forge V3 - Kernel-Only Contraction

## Summary

Forge was narrowed to a kernel-only product line.
The shipped surface became `forge-core`, `forge-codex`, and `forge-antigravity`.
This tranche removed runtime-tool and companion expectations from repo-root release, install, verify, and docs surfaces.
It is complete; current maintainer guidance now lives in `docs/current/*` and `packages/forge-core/references/target-state.md`.

## Scope

- updated roadmap references from V2 to V3 during the contraction cut
- shrank shipped bundle and release/install/verify contracts to 3 bundles
- removed runtime-tool and companion references from repo-root docs, tests, and scripts
- kept package-level refactors out of this slice

## Phases

### Phase A: Roadmap reset

- published this file as the contraction roadmap for the cut
- marked the previous V2 roadmap as historical and superseded
- pointed the current docs spine at the contraction outcomes

### Phase B: Bundle contraction

- keep only `forge-core`, `forge-codex`, and `forge-antigravity` in `docs/release/package-matrix.json`
- remove browse/design/companion install and verify expectations from root scripts
- keep release verification focused on the three shipped bundles

### Phase C: Maintainability pass

- trim root docs to the kernel-only story
- keep source-repo operator guidance centered on `scripts/repo_operator.py`
- remove stale runtime-tool and companion references from repo-root tests

## Verification

- `python scripts/verify_repo.py --profile fast`
- `python scripts/verify_repo.py --format json`
- root test files that encode release/install contracts
