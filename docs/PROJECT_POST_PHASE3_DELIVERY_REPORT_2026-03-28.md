# Post-Phase-3 Delivery Report

Date: 2026-03-28
Status: completed for the requested A1 to D3 batch
Scope:
- A1 real-repo canary and evidence capture
- A2 to A5 harden the first-party `nextjs-typescript-postgres` lane
- B1 to B3 operator UX and lifecycle surface
- C1 to C4 stronger shipping intelligence
- D1 to D3 lane scoring and gate decision

## Bottom Line

This batch is complete at the repo level.

Forge now has:
- a deeper first-party Next.js companion with auth, billing, and deploy-observability surfaces
- companion-aware operator context in `doctor`, `map-codebase`, and `dashboard`
- stronger companion lifecycle UX with inspect, upgrade, compatibility, and stale-registry handling
- authenticated QA packet preflight for `forge-browse`
- more useful release-doc drift and release-readiness behavior for auth and billing work
- lane scoring and lane-2 gate scripts
- real canary evidence on one external Next.js repo plus scaffold smoke on generated lane workspaces

The lane-2 gate currently fails on purpose:
- candidate scoring exists
- one candidate is strong
- but shipping intelligence is not yet tuned enough from real usage to justify opening lane 2

## Delivered

### A1. Real-repo canary and evidence

Real workspaces exercised:
- Forge repo itself
- external repo: `.tmp/nextjs-postgres-auth-starter`

Signals captured:
- `doctor`
- `map-codebase`
- `run_workspace_canary`
- `review_pack`
- `release_doc_sync`
- `release_readiness`
- authenticated QA packet creation and preflight through `forge-browse`

What the external repo showed:
- companion matched as `strong`
- operator profile resolved to `nextjs-prisma-app-router`
- verification pack resolved to `nextjs-production-ready`
- auth doc drift on `middleware.ts` was flagged with required doc categories `readme`, `architecture`, and `planning`
- release readiness failed because rollout evidence was still too thin

Why this matters:
- this is no longer a purely synthetic lane story
- Forge now has real friction data from a public Next.js repo

### A2 to A5. Harder lane-1 companion

Companion package affected:
- `packages/forge-nextjs-typescript-postgres`

What shipped:
- deeper `auth-saas`
- deeper `billing-saas`
- new `deploy-observability` preset
- richer capability metadata, command profiles, verification packs, doctor enrichers, and map enrichers
- stronger example and scaffold surface inside the companion package

Scaffold smoke performed:
- generated billing workspace through core init plus companion preset
- generated deploy-observability workspace through core init plus companion preset

Evidence from generated workspaces:
- billing scaffold resolved to `nextjs-billing-prisma-app-router` and `nextjs-billing-ready`
- observability scaffold resolved to `nextjs-observability-prisma-app-router` and `nextjs-observability-ready`

### B1. Companion-aware operator surface

Core files affected:
- `packages/forge-core/scripts/companion_operator_context.py`
- `packages/forge-core/scripts/doctor_companion.py`
- `packages/forge-core/scripts/doctor_report.py`
- `packages/forge-core/scripts/map_codebase.py`
- `packages/forge-core/scripts/map_codebase_report.py`
- `packages/forge-core/scripts/dashboard_support.py`

What changed:
- matched companions now expose operator profile and verification pack
- `doctor` text output shows profile and pack directly
- `map-codebase` persists verification-pack context into the codebase summary
- `dashboard` shows companion operator context instead of only companion ids

### B2. Companion lifecycle UX

Repo-level files affected:
- `scripts/install_bundle.py`
- `scripts/install_bundle_runtime.py`
- `scripts/install_bundle_report.py`
- `scripts/companion_install_support.py`
- release repo tests for install and companion install

What changed:
- install flow now supports inspect and upgrade behavior for companions
- compatibility report is visible in inspect mode
- stale registry replacement is explicit instead of silent
- install manifest records mode, compatibility, and transition state

Important current signal:
- inspect of `forge-nextjs-typescript-postgres` reports compatibility `WARN`
- reason: `forge-core` is `1.4.1`, companion support range still says `0.1.0 - 0.x`

This is useful because:
- Forge now reports the truth instead of pretending the versions are aligned

### B3. Entry docs

New docs:
- `docs/QUICKSTART_SOLO_DEV_SHIPPING_2026-03-28.md`
- `docs/COMPANION_DECISION_GUIDE_2026-03-28.md`
- `docs/TROUBLESHOOTING_2026-03-28.md`

What they cover:
- core vs companion path
- current first-party lane usage
- common failure modes for runtime tools, companion profiles, readiness, and QA packets

### C1. Authenticated QA packets

Browse package affected:
- `packages/forge-browse/scripts/browse_packets.py`
- `packages/forge-browse/scripts/forge_browse.py`
- browse tests and README

What changed:
- QA packets can now declare authenticated flows
- packet metadata includes login URL and storage-state requirements
- `qa-run` performs deterministic preflight before any runtime action

Real evidence:
- created packet `auth-dashboard-smoke`
- packet run failed fast on missing storage state
- this is the intended behavior for a private flow without a prepared browser session

### C2. Stronger release-doc sync

Core script affected:
- `packages/forge-core/scripts/release_doc_sync.py`

What changed:
- new rules for auth surface
- new rules for billing surface
- new rules for observability or health surface
- report now exposes matched rules and coverage gaps

### C3. Stronger release readiness

Core script affected:
- `packages/forge-core/scripts/release_readiness.py`

What changed:
- new profiles `auth` and `billing`
- `auto` profile now resolves from detected lane features
- review-pack evidence can now be required
- missing evidence is reported explicitly

Real evidence:
- external repo readiness stayed blocked by rollout-evidence thresholds even after quality gate, docs sync, review pack, and workspace canary artifacts existed

### C4. Sharper review pack

Core script affected:
- `packages/forge-core/scripts/review_pack.py`

What changed:
- new auth check for callback or base URL documentation
- new billing check for publishable key documentation
- new billing check for an obvious webhook route
- explicit recommended follow-ups when findings exist

### D1 and D2. Lane scoring

New scripts:
- `packages/forge-core/scripts/lane_score.py`
- `packages/forge-core/scripts/lane_gate.py`

Candidate scores recorded:
- `electron-react-postgres`: `68.0`, recommendation `consider`
- `vite-capacitor-supabase`: `78.0`, recommendation `strong`

Current interpretation:
- `vite-capacitor-supabase` has stronger product pull right now because it matches LamDiFood-style local-first operational apps
- Electron remains viable, but it is not the strongest next lane from the evidence currently in hand

### D3. Lane-2 gate decision

Gate result:
- `FAIL`

Why it failed:
- shipping intelligence is not yet tuned enough from real usage

Current next action:
- continue hardening lane 1

## Real Evidence Highlights

Forge repo:
- `doctor`: `WARN` only because runtime tool registry path is not configured
- `run_workspace_canary`: `pass`

External Next.js repo:
- `doctor`: `WARN` only for runtime tool registry, companion detection was `strong`
- `map-codebase`: `PASS`
- `review_pack`: `PASS`
- `release_doc_sync`: `WARN` on auth doc drift
- `release_readiness`: `FAIL` because rollout evidence is too thin

Generated billing scaffold:
- `doctor`: resolved `nextjs-billing-prisma-app-router`
- verification pack: `nextjs-billing-ready`

Generated observability scaffold:
- `doctor`: resolved `nextjs-observability-prisma-app-router`
- verification pack: `nextjs-observability-ready`

Authenticated QA packet:
- packet created successfully
- packet run failed fast because storage state did not exist yet

## Verification

Package-level tests:
- `python -m pytest packages/forge-core/tests -q` -> `127 passed, 5 skipped, 206 subtests passed`
- `python -m pytest packages/forge-browse/tests -q` -> `16 passed`
- `python -m pytest packages/forge-nextjs-typescript-postgres/tests -q` -> `16 passed, 8 subtests passed`
- `python -m pytest tests/release_repo_test_install.py tests/release_repo_test_companion_install.py tests/release_repo_test_contracts.py -q` -> `21 passed, 3 subtests passed`

Bundle and repo verification:
- `python packages/forge-core/scripts/verify_bundle.py --format json` -> `PASS`
- `python packages/forge-browse/scripts/verify_bundle.py --format json` -> `PASS`
- `python packages/forge-nextjs-typescript-postgres/scripts/verify_bundle.py --format json` -> `PASS`
- `python scripts/verify_repo.py --format json` -> `PASS`

Install lifecycle smoke:
- `python scripts/install_bundle.py forge-nextjs-typescript-postgres --target <temp> --inspect --format json` -> exit `0`, compatibility `WARN`, transition `inspect`

## Residual Risk

- companion version compatibility still warns because the companion contract range does not match the current core version
- authenticated browser QA still needs a real live app plus prepared storage state for full end-to-end proof
- release readiness on the external repo is still blocked by thin rollout evidence, which is the correct outcome
- lane 2 remains intentionally closed even though one candidate scores strongly

## Recommended Next Step

Do not open lane 2 yet.

Next highest-value work:
1. run more real-repo canaries on the current lane
2. tune release readiness and QA from those real repos
3. align companion compatibility versioning with the current core line
