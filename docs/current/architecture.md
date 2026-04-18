# Forge Current Architecture

## Goal

Describe the current maintainer-facing structure of Forge without forcing readers through archived roadmap or spec history.

## Current topology

- `packages/forge-core/` owns routing, workflow-state, verification discipline, and the host-neutral execution contract.
- `packages/forge-codex/overlay/` and `packages/forge-antigravity/overlay/` adapt that core contract to host-native entry surfaces.
- The shipped product line is kernel-only: `forge-core`, `forge-codex`, and `forge-antigravity`.
- `docs/current/` is the active maintainer docs spine.
- `docs/archive/` holds historical plans and specs that should not be read as current operating policy.

## Current source-of-truth boundaries

- Current repo-level architecture guidance lives here and in `packages/forge-core/references/target-state.md`.
- Current source-repo operator guidance lives in `docs/current/operator-surface.md`.
- Current install and activation guidance lives in `docs/current/install-and-activation.md`.
- Historical roadmap shaping and exploratory specs live under `docs/archive/` and should be cited only as historical context.

## Explicit non-changes in this tranche

- bundle fingerprints remain canonical
- `verify_repo.py` remains the release gate
- install safety and backup behavior remain intact
- installed runtime workflow paths remain stable

## Current maintenance posture

- no active roadmap tranche is open; `docs/current/*` plus `packages/forge-core/references/target-state.md` are the live maintainer source of truth
- changes should default to drift correction, compatibility repair, and verification hardening
- source-repo operator guidance stays centered on `scripts/repo_operator.py`
- release and install contracts stay aligned with the three-bundle product line
