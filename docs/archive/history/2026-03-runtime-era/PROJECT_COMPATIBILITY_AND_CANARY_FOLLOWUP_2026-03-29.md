# Project Compatibility And Canary Follow-Up

Date: 2026-03-29
Scope: close the companion compatibility warning, restate fresh verification, and consolidate recent canary evidence before any lane-2 decision.

## Objective

This follow-up closes the known compatibility warning on `forge-nextjs-typescript-postgres` and records the latest canary evidence already gathered during the post-Phase-3 hardening pass.

The target was not to reopen Phase 2 or Phase 3. The target was narrower:

- align companion compatibility metadata with the current Forge core release;
- lock that alignment with tests so the warning does not regress silently;
- restate real-repo and scaffold evidence already produced;
- confirm whether the lane-2 gate should change.

## Changes Made

### 1. Companion compatibility metadata now matches Forge core

Updated:

- `packages/forge-nextjs-typescript-postgres/data/companion-capabilities.json`

Changes:

- companion `version` changed from `0.1.0` to `1.4.1`;
- compatibility lower bound changed to `forge_core_min = 1.4.1`;
- compatibility upper bound changed to `forge_core_max = 1.x`.

Result:

- `install_bundle.py --inspect` no longer reports a compatibility warning for the first-party companion against the current core release.

### 2. Contract tests now enforce version alignment

Updated:

- `packages/forge-nextjs-typescript-postgres/tests/test_contracts.py`

Added assertions:

- companion capabilities version must equal repo `VERSION`;
- `forge_core_min` must equal repo `VERSION`;
- `forge_core_max` must remain `1.x`.

Result:

- future release bumps should fail fast if the companion metadata is not updated with the core version.

### 3. Install-flow tests now expect the corrected compatibility outcome

Updated:

- `tests/release_repo_test_install.py`
- `tests/release_repo_test_companion_install.py`

Changes:

- compatibility expectation changed from `WARN` to `PASS`;
- compatibility message expectation now checks the explicit compatible verdict.

Result:

- release/install regression tests now encode the intended behavior instead of preserving the old warning.

## Fresh Verification

### Narrow tests rerun after the fix

Command:

```powershell
python -m pytest packages/forge-nextjs-typescript-postgres/tests/test_contracts.py -q
```

Result:

- `2 passed, 8 subtests passed`

Command:

```powershell
python -m pytest tests/release_repo_test_install.py tests/release_repo_test_companion_install.py -q
```

Result:

- `9 passed`

### Companion bundle verification

Command:

```powershell
python packages/forge-nextjs-typescript-postgres/scripts/verify_bundle.py --format json
```

Result:

- `PASS`

### Install inspect smoke

Command:

```powershell
python scripts/install_bundle.py forge-nextjs-typescript-postgres --target $env:TEMP\forge-companion-inspect --inspect --build --format json
```

Result:

- compatibility `status = PASS`
- `core_version = 1.4.1`
- `companion_version = 1.4.1`
- compatibility range = `1.4.1 - 1.x`
- message = `forge-core 1.4.1 is compatible with companion 1.4.1.`

## Consolidated Canary Evidence

This section restates the canary and scaffold evidence already produced in the previous hardening pass. The goal is to keep the lane decision grounded in recorded artifacts instead of chat memory.

### A. External real-repo canary

Workspace:

- `.tmp/nextjs-postgres-auth-starter`

Evidence:

- workspace canary status = `pass`
- summary = `Core routing pack passed on nextjs-postgres-auth-starter (5/5 scenarios).`
- detected runtime = `node-ts`
- the build scenario required `change_artifacts_required = true`
- the deploy scenario correctly routed through `secure + quality-gate + deploy`

Interpretation:

- Forge core routing remains healthy on a real external Next.js and Postgres shaped repo.
- The routing system is still using the right delivery discipline on large build slices.

### B. Release-doc sync on the external repo

Evidence:

- status = `WARN`
- changed path detected = `middleware.ts`
- matched rule = `auth-surface`
- suggested docs = `readme`, `architecture`, `planning`

Interpretation:

- the heuristic is doing useful work;
- it correctly treats auth or route-protection changes as documentation-sensitive;
- this is a real warning, not a false positive to suppress.

### C. Release readiness on the external repo

Evidence:

- status = `FAIL`
- workspace canary = `PASS`
- review pack = `PASS`
- release-doc sync = `WARN`
- rollout readiness blocker = `Need at least 2 workspaces, found 1.; Need at least 2 total canary runs, found 1.`

Interpretation:

- the readiness gate is behaving correctly;
- one good workspace is not enough to claim broader rollout readiness.

### D. Generated billing scaffold evidence

Workspace:

- `.tmp/generated-billing-app`

Evidence:

- companion strength = `strong`
- profile = `nextjs-billing-prisma-app-router`
- verification pack = `nextjs-billing-ready`
- detected product features = `auth`, `billing`

Interpretation:

- the billing preset is not just generating files;
- it is producing a workspace that the companion can classify and operate on with a specific verification pack.

### E. Generated observability scaffold evidence

Workspace:

- `.tmp/generated-observability-app`

Evidence:

- companion strength = `strong`
- profile = `nextjs-observability-prisma-app-router`
- verification pack = `nextjs-observability-ready`
- detected product feature = `observability`

Interpretation:

- the observability preset is coherent with the companion detection and operator contract;
- this is useful evidence that lane depth is improving, not just breadth.

## Lane-2 Gate Status

Current gate artifact:

- `.tmp/lane-gate.json`

Recorded verdict:

- `status = FAIL`
- candidate = `vite-capacitor-supabase`
- candidate score = `78.0`
- blocker = `Shipping intelligence has not been tuned from real usage yet.`

Interpretation:

- the compatibility fix does not change the gate result;
- the blocker is not versioning anymore;
- the blocker is still depth of real-world shipping evidence on lane 1.

## Conclusion

This follow-up closes the only known false warning in the companion install story. The first-party `nextjs-typescript-postgres` companion is now version-aligned with Forge core, and the alignment is protected by tests.

The broader product conclusion does not change:

- lane 1 is healthier than before;
- canary and scaffold evidence are real and useful;
- lane 2 should still remain closed until shipping intelligence is tuned with more live usage and more than one real workspace.

## Immediate Next Step

The next best move is still the same:

- run at least one additional real-repo canary with the current lane-1 companion;
- then rerun release readiness and the lane-2 gate with broader rollout evidence.
