# Phase 2 Implementation Report

Date: 2026-03-28
Status: Completed
Scope:
- first-party `nextjs-typescript-postgres` companion bundle
- companion-aware core surfaces for `init`, `doctor`, `map-codebase`, and route preview
- release, install, and verification pipeline support for the new companion bundle

Inputs:
- [2026-03-28-forge-solo-dev-roadmap.md](plans/2026-03-28-forge-solo-dev-roadmap.md)
- [2026-03-28-nextjs-typescript-postgres-companion.md](archive/specs/2026-03-28-nextjs-typescript-postgres-companion.md)

## Summary

Phase 2 is complete at the repo level.

Forge now has a real first-party companion for the first optimized solo-dev path:
- `Next.js`
- `TypeScript`
- `Postgres`

This was implemented without turning `forge-core` into a web-specific framework.

The split is now real in code:
- `forge-core` remains the orchestrator
- `forge-nextjs-typescript-postgres` supplies stack-specific presets, commands, doctor enrichers, map enrichers, and verification data

This is the first time Forge has a concrete golden path while still preserving companion-based extensibility.

## Delivered Work

### 1. First-Party Companion Bundle

New package:
- `packages/forge-nextjs-typescript-postgres/`

Core companion files:
- `packages/forge-nextjs-typescript-postgres/companion.json`
- `packages/forge-nextjs-typescript-postgres/SKILL.md`
- `packages/forge-nextjs-typescript-postgres/data/companion-capabilities.json`
- `packages/forge-nextjs-typescript-postgres/data/command-profiles.json`
- `packages/forge-nextjs-typescript-postgres/data/verification-packs.json`

Preset and example surface:
- `packages/forge-nextjs-typescript-postgres/templates/minimal-saas/*`
- `packages/forge-nextjs-typescript-postgres/examples/minimal-saas/README.md`

Deterministic helpers:
- `packages/forge-nextjs-typescript-postgres/scripts/companion_common.py`
- `packages/forge-nextjs-typescript-postgres/scripts/resolve_commands.py`
- `packages/forge-nextjs-typescript-postgres/scripts/enrich_doctor.py`
- `packages/forge-nextjs-typescript-postgres/scripts/enrich_map_codebase.py`
- `packages/forge-nextjs-typescript-postgres/scripts/scaffold_preset.py`
- `packages/forge-nextjs-typescript-postgres/scripts/verify_bundle.py`

Behavior:
- defines one machine-readable capability manifest for the companion
- ships one initial preset: `minimal-saas`
- resolves command profiles and verification packs for a Next.js plus Prisma baseline
- emits stack-specific doctor checks
- emits stack-specific map-codebase enrichments
- verifies itself independently with a bundle-local test suite

### 2. Core Companion Discovery And Invocation

New core files:
- `packages/forge-core/scripts/companion_catalog.py`
- `packages/forge-core/scripts/companion_matching.py`
- `packages/forge-core/scripts/companion_invoke.py`

Behavior:
- discovers companion bundles from sibling package roots or explicit companion paths
- matches companions from prompt text, repo signals, package dependencies, and file markers
- resolves preset selectors such as `nextjs-typescript-postgres/minimal-saas`
- invokes companion scripts through manifest-declared capability hooks instead of hardcoding Next.js logic inside core

### 3. Companion-Aware Core Surfaces

Changed core files:
- `packages/forge-core/scripts/initialize_workspace.py`
- `packages/forge-core/scripts/doctor.py`
- `packages/forge-core/scripts/doctor_report.py`
- `packages/forge-core/scripts/map_codebase.py`
- `packages/forge-core/scripts/map_codebase_report.py`
- `packages/forge-core/scripts/route_preview.py`

Behavior:
- `initialize_workspace.py` now accepts optional companion presets and keeps the core report shape
- `doctor.py` detects matching first-party companions and appends stack-specific checks
- `map_codebase.py` merges companion enrichments into stack and structure reports
- `route_preview.py` exposes first-party companion activation in routing output and activation lines
- core still owns evidence, reporting, complexity, and workflow gates

### 4. Release And Install Integration

Changed release files:
- `docs/release/package-matrix.json`
- `scripts/release_package_specs.py`
- `scripts/build_release.py`
- `scripts/verify_repo.py`

Changed release tests:
- `tests/release_repo_test_contracts.py`
- `tests/release_repo_test_install.py`

Behavior:
- adds a new bundle to the package matrix with `host: companion`
- teaches release discovery to load `companion.json`
- builds `forge-nextjs-typescript-postgres` into `dist/`
- includes the companion in repo verification and dry-run install coverage
- proves install manifests work for explicit companion targets

### 5. Regression Coverage

New or changed core tests:
- `packages/forge-core/tests/test_initialize_workspace.py`
- `packages/forge-core/tests/test_doctor.py`
- `packages/forge-core/tests/test_map_codebase.py`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/fixtures/workspaces/nextjs_postgres_workspace/*`
- `packages/forge-core/tests/fixtures/help_next_cases.json`

New companion tests:
- `packages/forge-nextjs-typescript-postgres/tests/test_contracts.py`
- `packages/forge-nextjs-typescript-postgres/tests/test_init_preset.py`
- `packages/forge-nextjs-typescript-postgres/tests/test_command_profiles.py`
- `packages/forge-nextjs-typescript-postgres/tests/test_doctor_and_map.py`

Behavior covered:
- preset-aware init
- companion-aware doctor
- companion-aware map-codebase
- first-party companion detection in route preview
- release build and install of the companion bundle

## Verification

Primary core verification:

```text
python -m pytest packages/forge-core/tests -q
Result: 111 passed, 5 skipped, 192 subtests passed in 15.33s
```

Companion bundle verification:

```text
python packages/forge-nextjs-typescript-postgres/scripts/verify_bundle.py --format json
Result: PASS
Details: py_compile PASS, unittest PASS, 6 tests passed
```

Release and install regression verification:

```text
python -m unittest tests/test_release_repo.py -v
Result: PASS
Details: 21 tests passed
```

Dist core verification after release build:

```text
python dist/forge-core/scripts/verify_bundle.py --format json
Result: PASS
Details: py_compile PASS, unittest PASS, smoke_matrix PASS
```

Repo-level verification:

```text
python scripts/verify_repo.py --format json
Result: PASS
Details: generated_host_artifacts PASS, repo.py_compile PASS, repo.unittest PASS, forge-core.verify_bundle PASS, build_release PASS, install dry runs PASS, dist bundle verification PASS
```

## Phase 2 Exit Criteria Check

- first-party companion package exists: yes
- `forge-core` remains orchestrator and does not hardcode Next.js routing policy: yes
- init can scaffold the first optimized path via companion preset: yes
- doctor and map-codebase can consume companion enrichments: yes
- route preview exposes first-party companion activation: yes
- release build and install pipeline recognize the companion bundle: yes
- repo-level verification stays green with the new bundle: yes

## Residual Risk

- the new companion ships only one preset and one reference product shape; auth, billing, and deploy vendor presets are still future work
- companion discovery currently prefers sibling bundle locations and explicit companion paths; there is not yet a dedicated companion registry state file
- explicit install works, but there is not yet a `doctor` or `stack-set` UX for companion installation
- the workspace still has unrelated untracked artifacts from earlier work, including `.tmp/` and prior Phase 1 docs/code that were already present before this Phase 2 closeout

## Bottom Line

Phase 2 is complete.

Forge now has:
- a first real companion bundle
- a real preset-aware init path
- real stack-aware doctor and map enrichment
- route preview awareness of first-party companions
- release and install coverage for the new bundle

Most importantly, this was done without collapsing `forge-core` into a Next.js framework.

Forge is now structurally closer to the intended model:
- `forge-core` as orchestrator
- first-party companions as optimized solo-dev product paths
