Date: 2026-04-11
Status: current roadmap

# Forge V3 - Kernel-Only Contraction

## Summary

Forge is being narrowed to a kernel-only product line.
The shipped surface becomes `forge-core`, `forge-codex`, and `forge-antigravity`.
This tranche removes runtime-tool and companion expectations from repo-root release, install, verify, and docs surfaces.

## Scope

- update current roadmap references from V2 to V3
- shrink shipped bundle and release/install/verify contracts to 3 bundles
- remove runtime-tool and companion references from repo-root docs, tests, and scripts
- keep package-level refactors out of this slice

## Phases

### Phase A: Roadmap reset

- publish this file as the current roadmap
- mark the previous V2 roadmap as historical and superseded
- keep the current docs spine pointed at V3

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

