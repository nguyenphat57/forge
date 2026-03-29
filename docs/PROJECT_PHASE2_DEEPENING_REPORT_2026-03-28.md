# Project Phase 2 Deepening Report

Date: 2026-03-28
Scope: deepen the first-party `nextjs-typescript-postgres` companion so it is more ship-ready, and finish companion install plus doctor UX in `forge-core`

## Goal

Complete the next build slice after the initial Phase 2 lane launch:

- add stronger product presets in the first-party companion
- make companion install and registration meaningful for installed adapters
- make `doctor` report active companion install state
- keep `forge-core` lane-agnostic while allowing first-party companions to inject deeper product paths

## Delivered

### 1. Registry-aware companion discovery in core

`forge-core` companion discovery now reads registered companion targets from adapter state instead of relying only on repo-local or dist-neighbor package paths.

Changed files:

- `packages/forge-core/scripts/companion_catalog.py`
- `packages/forge-core/scripts/companion_registry.py`

What changed:

- companion registry records can now contribute real candidate roots for discovery
- stale registered paths are ignored safely instead of crashing discovery
- installed adapters can discover companions that live outside the bundle tree as long as they are registered

Why this matters:

- companion install is now operationally useful, not just bookkeeping
- installed Codex and Antigravity bundles can use registered companions without depending on monorepo-relative package layout

### 2. Doctor now reports companion registry state clearly

`doctor` already had companion hooks; this batch closes the UX loop by making registry state explicit in the report and testing the registered-state path.

Changed files:

- `packages/forge-core/scripts/doctor.py`
- `packages/forge-core/scripts/doctor_companion.py`
- `packages/forge-core/scripts/doctor_report.py`
- `packages/forge-core/tests/test_doctor.py`

What changed:

- `doctor` returns `companions` and `companion_registry` sections in JSON
- text output shows companion summary and registry path
- tests now cover registered companion state, not only local bundle detection

### 3. New first-party presets: auth and billing

The `nextjs-typescript-postgres` companion now ships three preset tracks instead of only the minimal baseline.

Changed files:

- `packages/forge-nextjs-typescript-postgres/data/companion-capabilities.json`
- `packages/forge-nextjs-typescript-postgres/data/command-profiles.json`
- `packages/forge-nextjs-typescript-postgres/data/verification-packs.json`
- `packages/forge-nextjs-typescript-postgres/scripts/companion_common.py`
- `packages/forge-nextjs-typescript-postgres/scripts/resolve_commands.py`
- `packages/forge-nextjs-typescript-postgres/scripts/enrich_doctor.py`
- `packages/forge-nextjs-typescript-postgres/scripts/enrich_map_codebase.py`
- `packages/forge-nextjs-typescript-postgres/templates/auth-saas/*`
- `packages/forge-nextjs-typescript-postgres/templates/billing-saas/*`
- `packages/forge-nextjs-typescript-postgres/examples/auth-saas/README.md`
- `packages/forge-nextjs-typescript-postgres/examples/billing-saas/README.md`

New preset surface:

- `minimal-saas`
- `auth-saas`
- `billing-saas`

New behavior:

- feature detection now recognizes `auth` and `billing`
- command resolution can choose:
  - `nextjs-prisma-app-router`
  - `nextjs-auth-prisma-app-router`
  - `nextjs-billing-prisma-app-router`
- verification pack resolution can choose:
  - `nextjs-production-ready`
  - `nextjs-auth-ready`
  - `nextjs-billing-ready`
- doctor enrichers now check `AUTH_SECRET` and Stripe env keys when those features exist
- map-codebase enrichers now annotate auth and billing entrypoints, integrations, and next actions

### 4. Companion install and host registration UX

Install flow now supports companion registration into host adapter state.

Changed files:

- `scripts/companion_install_support.py`
- `scripts/install_bundle_runtime.py`
- `scripts/install_bundle.py`
- `tests/release_repo_test_install.py`

What changed:

- new install flags:
  - `--register-codex-companion`
  - `--register-gemini-companion`
- install manifest records companion registration metadata
- install reporting now prints companion registry destinations
- root integration tests verify that an installed Codex bundle can discover a registered companion outside the bundle tree

### 5. Init coverage for deeper presets

Core init flow remains generic, but companion-aware preset application now has deeper coverage.

Changed files:

- `packages/forge-core/tests/test_initialize_workspace.py`
- `packages/forge-nextjs-typescript-postgres/tests/test_init_preset.py`

What changed:

- core init tests now cover the billing preset path
- companion tests now scaffold and assert all three presets

### 6. Release verification surface updated

Release packaging now explicitly guards the new preset surfaces.

Changed files:

- `docs/release/package-matrix.json`
- `tests/release_repo_test_contracts.py`

What changed:

- auth and billing templates are now required bundle paths
- auth and billing example README paths are now required bundle paths
- release contract tests assert the deeper companion bundle surface

## Verification

### Targeted verification

Command:

`python -m pytest packages/forge-core/tests/test_companion_registry.py packages/forge-core/tests/test_doctor.py packages/forge-core/tests/test_initialize_workspace.py -q`

Result:

- `13 passed, 2 subtests passed`

Command:

`python -m pytest packages/forge-nextjs-typescript-postgres/tests/test_contracts.py packages/forge-nextjs-typescript-postgres/tests/test_init_preset.py packages/forge-nextjs-typescript-postgres/tests/test_command_profiles.py packages/forge-nextjs-typescript-postgres/tests/test_doctor_and_map.py -q`

Result:

- `12 passed, 6 subtests passed`

Command:

`python -m pytest tests/release_repo_test_install.py tests/release_repo_test_contracts.py -q`

Result:

- `18 passed, 3 subtests passed`

Notable integration proof:

- installed `forge-codex` bundle successfully discovered a registered `forge-nextjs-typescript-postgres` companion outside the bundle tree

### Bundle and repo verification

Command:

`python packages/forge-nextjs-typescript-postgres/scripts/verify_bundle.py --format json`

Result:

- `PASS`

Command:

`python -m pytest packages/forge-core/tests -q`

Result:

- `115 passed, 5 skipped, 194 subtests passed`

Command:

`python scripts/verify_repo.py --format json`

Result:

- `PASS`

This final repo verification also exercised:

- host artifact freshness
- repo py_compile
- repo unittest
- secret scan
- release build
- dry-run install paths for adapters, runtime tools, and the companion bundle
- dist bundle verification for all bundles

## Outcome

The first-party lane is now deeper in the right place:

- richer preset surface for real product work
- companion install path that actually affects installed adapters
- stronger doctor visibility for companion state
- release and repo verification that protect the new surface

This keeps `forge-core` as the orchestrator kernel while moving stack depth into the companion layer, which is the intended architecture.

## Residual risk

- The companion is deeper, but still not a full product lane yet; auth and billing are scaffold-level foundations, not complete production integrations.
- There is still only one first-party companion lane. Cross-lane policy and compatibility rules are still mostly future work.
- `.tmp/` remains untracked in the worktree from earlier external repo research and was not touched by this batch.
- Existing pre-batch worktree modifications outside this slice were left intact on purpose.
