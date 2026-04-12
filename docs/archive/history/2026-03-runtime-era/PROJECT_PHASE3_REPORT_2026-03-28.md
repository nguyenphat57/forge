# Project Phase 3 Report

Date: 2026-03-28
Scope: complete the product-ready shipping intelligence slice on top of the finished foundation and the first-party Next.js companion lane

## Goal

Make Forge more trustworthy for a solo dev shipping and checking a real product by adding:

- a terminal-first dashboard
- reusable browser QA packets on persistent sessions
- release-doc drift checks
- release-readiness aggregation on top of gates and canaries
- a reusable solo-dev review pack

## Delivered

### 1. Dashboard

New files:

- `packages/forge-core/scripts/dashboard.py`
- `packages/forge-core/scripts/dashboard_support.py`
- `packages/forge-core/workflows/operator/dashboard.md`
- `packages/forge-core/tests/test_dashboard.py`

What shipped:

- terminal-first workspace dashboard from durable artifacts
- current stage, focus, next workflow, and recommended action
- continuity counts from `.brain/decisions.json` and `.brain/learnings.json`
- latest plan/spec and codebase map visibility
- active change visibility
- latest verification summary
- runtime tool resolution status
- companion matches
- latest release-doc sync, workspace canary, and release-readiness hints when present

Why it matters:

- solo-dev state is now inspectable without digging through multiple artifact folders manually

### 2. Stronger `forge-browse` QA

New files:

- `packages/forge-browse/scripts/browse_packets.py`
- `packages/forge-browse/tests/test_browse_packets.py`

Changed files:

- `packages/forge-browse/scripts/forge_browse.py`
- `packages/forge-browse/README.md`
- `packages/forge-browse/tests/test_browse_contracts.py`
- `docs/release/package-matrix.json`
- `tests/release_repo_test_contracts.py`

What shipped:

- reusable QA packets on top of persistent sessions
- new CLI surface:
  - `qa-create`
  - `qa-list`
  - `qa-run`
- packet mode `html-smoke` for deterministic open-and-assert loops
- packet mode `playwright-snapshot` for session-backed screenshot runs
- persisted QA packet definitions and run reports inside session artifacts

Why it matters:

- Forge now has a repeatable QA surface instead of only one-off browse actions
- persistent session state becomes more useful for actual release flows

### 3. Release-doc sync

New files:

- `packages/forge-core/scripts/release_doc_sync.py`
- `packages/forge-core/workflows/execution/release-doc-sync.md`
- `packages/forge-core/tests/test_release_doc_sync.py`

What shipped:

- drift check between changed release surfaces and changed docs surfaces
- heuristic coverage for:
  - product surface changes
  - database or migration changes
  - runtime/config changes
- explicit reporting of missing doc coverage
- suggestions for which doc categories to update:
  - `readme`
  - `architecture`
  - `release`
  - `planning`
- persisted latest/history artifacts under `.forge-artifacts/release-doc-sync/`

Why it matters:

- shipping no longer silently drifts away from docs when code, config, or schema changed

### 4. Release readiness

New files:

- `packages/forge-core/scripts/release_readiness.py`
- `packages/forge-core/workflows/execution/release-readiness.md`
- `packages/forge-core/tests/test_release_readiness.py`

Changed files:

- `packages/forge-core/scripts/run_workspace_canary_persist.py`

What shipped:

- readiness aggregation from:
  - latest quality gate
  - latest release-doc sync
  - latest workspace canary
  - rollout canary readiness
- profiles:
  - `standard`
  - `production`
- stricter production behavior for missing or warning-grade release signals
- persisted latest/history artifacts under `.forge-artifacts/release-readiness/`
- workspace canary persistence now also writes `latest.json` and `latest.md`

Why it matters:

- release state is now machine-readable instead of spread across unrelated artifacts

### 5. Solo-dev review pack

New files:

- `packages/forge-core/scripts/review_pack.py`
- `packages/forge-core/workflows/execution/review-pack.md`
- `packages/forge-core/tests/test_review_pack.py`

What shipped:

- reusable review pack artifact for pre-release work
- lane-aware checks from companion feature detection
- public-surface security-minded review focus
- auth-specific checks
- billing-specific checks
- migration safety reminders for Postgres-oriented work
- optional `adversarial` mode with stronger negative-path prompts
- findings when sensitive env documentation is missing, such as `AUTH_SECRET` or Stripe keys

Why it matters:

- review becomes a repeatable product surface instead of an ad-hoc ritual

## Verification

### Targeted Phase 3 tests

Command:

`python -m pytest packages/forge-core/tests/test_dashboard.py packages/forge-core/tests/test_release_doc_sync.py packages/forge-core/tests/test_release_readiness.py packages/forge-core/tests/test_review_pack.py -q`

Result:

- `7 passed`

Command:

`python -m pytest packages/forge-browse/tests/test_browse_packets.py packages/forge-browse/tests/test_browse_contracts.py packages/forge-browse/tests/test_browse_runtime.py -q`

Result:

- `7 passed`

### Broader package verification

Command:

`python -m pytest packages/forge-core/tests -q`

Result:

- `122 passed, 5 skipped, 203 subtests passed`

Command:

`python -m pytest packages/forge-browse/tests -q`

Result:

- `14 passed`

Command:

`python -m pytest tests/release_repo_test_contracts.py tests/release_repo_test_install.py -q`

Result:

- `18 passed, 3 subtests passed`

Command:

`python packages/forge-core/scripts/verify_bundle.py --format json`

Result:

- `PASS`

Command:

`python packages/forge-browse/scripts/verify_bundle.py --format json`

Result:

- `PASS`

Command:

`python scripts/verify_repo.py --format json`

Result:

- `PASS`

## Outcome

Phase 3 is now materially present in the repo:

- work state is visible through `dashboard`
- browser QA can be packetized and rerun
- release-doc drift can be checked explicitly
- release readiness can be aggregated from actual artifacts
- review can be packaged with lane-aware and adversarial checks

This pushes Forge closer to the intended shape:

- `forge-core` stays the orchestrator kernel
- runtime-tool specifics stay in `forge-browse`
- shipping intelligence is now built from durable artifacts rather than chat-only memory

## Residual risk

- `forge-browse` QA packets are useful now, but the strongest authenticated flow still depends on Playwright-backed session usage by the operator; the fully automated auth flow is not expanded beyond the current session persistence model.
- release-doc sync is heuristic by design; it surfaces likely drift and suggested doc categories, but it does not replace human editorial judgment.
- release-readiness is only as strong as the latest persisted artifacts; if a team skips quality gates or canaries, the report can only show that gap, not invent evidence.
- `.tmp/` remains untracked in the worktree from earlier external repo research and was left untouched.
- existing unrelated worktree changes outside this slice were preserved on purpose.
