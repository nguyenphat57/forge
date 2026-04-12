# Project Real-Repo Canary And Auth QA Report

Date: 2026-03-29
Scope: finish the next batch after the compatibility follow-up by adding more real-repo evidence, rerunning readiness and lane gates, upgrading authenticated QA, and cleaning redundant temporary outputs.

## Objective

This batch executed the exact next steps that were still open:

- add more real-repo canary evidence for lane 1;
- rerun release readiness and the lane gate with fresh evidence;
- make authenticated QA use the session storage state during runtime instead of only during preflight;
- clean redundant ad hoc temp outputs without deleting evidence still used by the reports and gates.

## Changes Made

### 1. Added more real-repo canary coverage

New public repos cloned under `.tmp/`:

- `prisma/fullstack-prisma-nextjs-blog`
- `nemanjam/nextjs-prisma-boilerplate`

Existing external repo reused:

- `nextjs-postgres-auth-starter`

All three real repos were mapped and matched the first-party companion strongly enough to count as lane-1 evidence.

### 2. Authenticated QA now uses session storage state during runtime

Added:

- `packages/forge-browse/scripts/browse_storage_state.py`
- `packages/forge-browse/scripts/browse_session_runtime.py`

Updated:

- `packages/forge-browse/scripts/browse_packets.py`
- `packages/forge-browse/tests/test_browse_packets.py`
- `packages/forge-browse/README.md`

Behavior change:

- authenticated QA packets no longer stop at `storage_state` existence checks;
- the runtime now loads matching cookies from Playwright-style `storage_state.json`;
- those cookies are applied during the HTML smoke request itself;
- the runtime records `driver = session-html-fetch` when auth storage is actually used.

This closes the previous gap where auth packets could report a preflight pass without proving the session state was applied at runtime.

### 3. Cleaned redundant ad hoc temp outputs

Removed:

- flat `.tmp/*.json` scratch outputs that already had persisted artifact replacements;
- random scratch directories with temporary names from previous experiments.

Kept intentionally:

- cloned public repos under `.tmp/`;
- generated example apps under `.tmp/`;
- `.tmp/lane-score-*.json`;
- `.tmp/lane-gate.json`;
- `.tmp/live-auth-qa-smoke.json`;
- persisted `.forge-artifacts/` and workspace-local `.forge-artifacts/` directories used by readiness and report flows.

## Real-Repo Evidence

### A. Controlled rollout canary status

Artifact:

- `.tmp/controlled-rollout-readiness.json`

Result:

- `status = PASS`
- `workspaces = 4`
- `total_runs = 5`
- `observation_days = 2`
- `fail_runs = 0`
- `warn_workspaces = 0`

Latest workspace runs included:

- `forge-core`
- `nextjs-postgres-auth-starter`
- `prisma-fullstack-prisma-nextjs-blog`
- `nemanjam-nextjs-prisma-boilerplate`

Interpretation:

- lane 1 now has enough multi-workspace canary evidence to satisfy the controlled-rollout threshold profile.

### B. Real-repo release readiness

Workspace:

- `.tmp/nextjs-postgres-auth-starter`

Artifact:

- `.tmp/nextjs-auth-release-readiness.json`

Result:

- `status = PASS`
- quality gate = `PASS`
- release-doc sync = `PASS`
- workspace canary = `PASS`
- review pack = `PASS`
- rollout readiness = `PASS`

Interpretation:

- the shipping-intelligence stack is no longer only theoretical on lane 1;
- it has now been rerun successfully on a real external repo with current evidence.

## Authenticated QA Evidence

Artifact:

- `.tmp/live-auth-qa-smoke.json`

Setup:

- a live local auth harness was started on `http://127.0.0.1:<port>`;
- `forge_browse.py` created a real session;
- the session `storage_state.json` was populated with a matching cookie;
- `qa-create` and `qa-run` were executed through the canonical CLI.

Result:

- `status = PASS`
- packet mode remained `html-smoke`
- preflight checks all passed
- runtime driver = `session-html-fetch`
- `cookie_header_applied = true`
- expected text `Welcome back` matched

Interpretation:

- authenticated QA is now using session state during runtime, not only as metadata;
- this is materially stronger evidence than the previous preflight-only behavior.

Residual limitation:

- this is still a session-backed HTML smoke, not full DOM automation of an interactive login sequence.
- Playwright-backed screenshot, PDF, open, and record flows still exist separately.

## Lane Gate

Artifact:

- `.tmp/lane-gate.json`

Result:

- `status = PASS`
- candidate = `vite-capacitor-supabase`
- `real_repo_count = 3`
- `example_app_complete = true`
- `operator_ux_ready = true`
- `shipping_intelligence_tuned = true`
- `candidate_score = 78.0`

Interpretation at the time of this run:

- after the new real-repo evidence and authenticated QA runtime fix, the previous evidence blocker was no longer present;
- the then-current lane-2 gate returned `PASS`.

Superseding policy note:

- the repo later narrowed this contract so that evidence alone is not enough;
- lane 2 now also requires explicit confirmation that product pull is stronger than more hardening on lane 1.

## Verification

Package-level verification:

- `python -m pytest packages/forge-browse/tests/test_browse_packets.py -q`
  - `5 passed`
- `python -m pytest packages/forge-browse/tests/test_browse_contracts.py -q`
  - `2 passed`
- `python packages/forge-browse/scripts/verify_bundle.py --format json`
  - `PASS`

Repo-level verification:

- `python scripts/verify_repo.py --format json`
  - `PASS`

Supporting runtime evidence:

- controlled rollout readiness JSON saved to `.tmp/controlled-rollout-readiness.json`
- release readiness JSON saved to `.tmp/nextjs-auth-release-readiness.json`
- live authenticated QA JSON saved to `.tmp/live-auth-qa-smoke.json`
- final lane gate JSON saved to `.tmp/lane-gate.json`

## Worktree Note

The worktree is still intentionally broad and dirty because the repo already contains many uncommitted Phase 1, 2, and 3 files plus current batch outputs.

This batch did not attempt to normalize the entire repo state or make commits. It only:

- added the auth-runtime fix in `forge-browse`;
- added fresh artifacts and docs for the current batch;
- removed redundant temporary scratch files that no longer carried unique evidence.

## Conclusion

This batch cleared the open items from the previous follow-up:

- lane 1 now has more than one real repo in controlled-rollout evidence;
- release readiness now passes on the external auth-shaped repo;
- authenticated QA now applies session storage at runtime;
- the historical lane-2 evidence gate passed under the contract that existed at the time of this run.

The remaining question is no longer only whether the current lane-1 evidence is enough.

The remaining question is product strategy:

- whether Forge should actually open `vite-capacitor-supabase` now;
- or deliberately keep hardening `nextjs-typescript-postgres` further before spending execution budget on lane 2.
