# Post-Phase-3 Implementation Backlog
Date: 2026-03-28
Status: historical backlog for the previous lane-first direction; see `docs/plans/2026-03-29-forge-process-first-roadmap.md` for current policy
Inputs:
- `docs/PRODUCT_THESIS_2026-03-28.md`
- `docs/plans/2026-03-28-forge-solo-dev-roadmap.md`
- `docs/PROJECT_PHASE2_DEEPENING_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE3_REPORT_2026-03-28.md`
## Goal
Turn the completed three-phase build into a harder, more usable product for real solo-dev shipping work.
This backlog is ordered by product leverage:
1. harden the existing golden path on real repos
2. improve operator UX and repeatability
3. strengthen shipping intelligence with real usage feedback
4. open a second lane only after explicit gates pass
## Sequencing Rules
1. Do not open lane 2 before lane 1 is used on real repos.
2. Do not add more abstraction layers before the current operator surface is easier to use.
3. Prefer real-repo evidence over synthetic completeness.
4. Every new preset or release check needs a matching verification path.
5. A passing lane-evidence gate is necessary but not sufficient; lane 2 still needs an explicit product-pull decision.
## Stage A: Harden Lane 1 On Real Repos
### A1. Real-repo canary for the Next.js companion
Why:
- current proof is strong at repo level, but the lane still needs real product pressure
Deliver:
- run the companion on Forge itself where applicable
- run the companion on one external Next.js product repo
- record friction, missing assumptions, and failed checks
Verify:
- each canary run produces `doctor`, `map-codebase`, change artifacts, QA packet, and release-readiness artifacts
Exit:
- at least one real repo can use the companion without process collapse
### A2. Harden `auth-saas`
Why:
- current auth preset is scaffold-level, not product-ready
Deliver:
- env contract for auth secrets and callback URLs
- session and middleware conventions
- auth-specific QA packet starter
- stronger auth review-pack checks

Verify:
- fixture failures for missing auth env, broken protected-route flow, and missing docs are caught

Exit:
- auth preset supports a believable v1 product flow
### A3. Harden `billing-saas`
Why:
- billing is a major trust boundary and still shallow in the current preset
Deliver:
- Stripe env and webhook contract
- billing event and reconciliation notes
- billing-specific QA packet starter
- stronger release-readiness checks for billing repos

Verify:
- fixture failures for missing Stripe secrets, missing webhook guidance, and billing doc drift are caught
Exit:
- billing preset is safe enough for guided solo-dev use
### A4. Add `deploy-observability` preset surface
Why:
- lane 1 still lacks a strong default story for runtime confidence after deployment

Deliver:
- env and deployment checklist
- production config notes
- basic error reporting and health-check guidance
- companion verification pack updates for deploy readiness

Verify:
- seeded missing env or missing deploy-doc cases fail readiness as expected

Exit:
- lane 1 has a visible path from local build to monitored deployment

### A5. Build one complete example app

Why:
- templates and presets are stronger when one end-to-end reference app proves the path

Deliver:
- one reference app using auth, billing, and Postgres
- matching quickstart and ship-a-v1 walkthrough
- seeded QA packet and release-doc examples

Verify:
- example app passes the lane verification pack and release-readiness flow

Exit:
- Forge can point to one concrete product path instead of separate preset fragments

## Stage B: Improve Operator UX

### B1. Companion-aware operator entry surface

Why:
- companion support is present but still too implicit for a solo developer

Deliver:
- clearer `doctor` summary for active companion and missing companion value
- clearer `map-codebase` note for matched companion and selected verification pack
- one operator doc that explains when the companion is active

Verify:
- text and JSON outputs expose the same companion state deterministically

Exit:
- operator can tell what Forge is assuming without reading bundle internals

### B2. Companion install and update workflow

Why:
- registration exists, but lifecycle UX still needs a tighter surface

Deliver:
- install, upgrade, and inspect commands for first-party companion packages
- compatibility report between `forge-core` and companion versions
- clearer failure messages for stale registry entries

Verify:
- integration tests cover install, upgrade, stale path, and incompatible version cases

Exit:
- companion lifecycle becomes routine instead of expert-only

### B3. Quickstart and decision guide

Why:
- current repo state is powerful, but the entry story is still too internal

Deliver:
- one top-level quickstart for solo-dev shipping
- one decision guide: core only vs companion lane
- one troubleshooting guide for common setup failures

Verify:
- docs checks confirm all linked commands and files exist

Exit:
- a new user can choose the right path without reading the whole repo

### B4. Governance artifact surfaces

Why:
- current repo-visible planning surfaces stop at `docs/`, `docs/plans/`, `docs/specs/`, and decisions or learnings
- the external audit also called for protected product intent and human-owned backlog patterns, but those are not yet shipped clearly

Deliver:
- one protected product-intent document template for lane-driven work
- document ownership notes that distinguish human-owned backlog surfaces from generated state
- one simple backlog convention that stays repo-visible and reviewable
- report evidence showing where these surfaces are created and how they are meant to be maintained

Verify:
- `init` or companion preset generation creates the promised governance files deterministically
- docs checks confirm those files are linked from the quickstart and decision guide

Exit:
- governance absorptions move from narrative-only to shipped evidence

## Stage C: Strengthen Shipping Intelligence

### C1. Authenticated `forge-browse` QA flows

Why:
- Phase 3 added reusable packets, but authenticated flows still rely too much on manual operator setup

Deliver:
- login-aware QA packet helpers
- session preflight checks
- fixture coverage for protected app flows

Verify:
- authenticated sample flow can run from persisted session state and report deterministic failures

Exit:
- browser QA becomes strong enough for real private app flows

### C2. Tune release-doc sync from real drift

Why:
- heuristic drift detection improves only when it sees real misses and false positives

Deliver:
- catalog of real doc-drift cases from canary repos
- refined mapping rules for code, config, schema, and public-surface changes
- better category suggestions in the report

Verify:
- regression fixtures cover at least three real drift patterns found during adoption

Exit:
- release-doc sync becomes more useful than noisy

### C3. Tighten release-readiness profiles

Why:
- readiness is only trustworthy when lane policies match real shipping expectations

Deliver:
- stricter profile for auth and billing apps
- explicit missing-evidence reasons in the final report
- clearer distinction between warning-grade and blocking gaps

Verify:
- seeded missing canary, missing docs, and missing quality-gate inputs produce the expected verdicts

Exit:
- release-readiness can be used as an actual pre-release check

### C4. Evolve the review pack from real findings

Why:
- review pack quality depends on whether it catches issues that actually matter in shipped repos

Deliver:
- add checks based on real auth, billing, migration, and env mistakes seen during canaries
- refine adversarial mode prompts for public-facing apps

Verify:
- regression fixtures show that new checks catch at least one real previously missed issue

Exit:
- review pack becomes sharper through actual shipping feedback

### C5. Strengthen the risk guard beyond the initial keyword pass

Why:
- the current `change_guard` is useful, but it is still only a first guardrail
- the audit chose privacy or risk guard behavior as a meaningful absorption, and the repo should either deepen it or keep calling it partial

Deliver:
- clearer rule groups for destructive filesystem actions, deploy actions, and secret-bearing changes
- report output that explains why an action was classified as `allow`, `warn`, or `block`
- updated docs that show this is a safety rail in the shipping system, not an invisible helper

Verify:
- seeded deploy, secret, and destructive-action cases classify deterministically in tests
- workflow docs and operator docs describe the same contract

Exit:
- the risk-guard absorption becomes explicit, test-backed, and no longer easy to miss in the product narrative

## Stage D: Decide Whether To Open Lane 2

### D1. Define lane scoring

Why:
- lane 2 should be chosen by product pull, not by curiosity

Deliver:
- a short scoring rubric based on:
  - number of real repos waiting for help
  - overlap with current core surfaces
  - companion feasibility
  - shipping leverage
  - maintenance cost

Verify:
- at least two candidate lanes can be scored consistently

Exit:
- lane choice becomes explicit and defensible

### D2. Score the main candidates

Why:
- the likely next candidates are already visible: desktop and local-first mobile-style apps

Deliver:
- score at least:
  - `electron-react-postgres`
  - `vite-capacitor-supabase`

Verify:
- each candidate produces a short decision memo with risks and why-now value

Exit:
- Forge has a grounded comparison instead of anecdotal preference

### D3. Open lane 2 only if gates pass

Gate:
- lane 1 is proven on real repos
- one example app is complete
- operator UX is clearer
- shipping intelligence has been tuned from real usage

If the gate fails:
- continue hardening lane 1

If the gate passes:
- start companion contract and package skeleton for the selected lane

## Immediate Next Build Order

1. A1 real-repo canary
2. A2 auth hardening
3. A3 billing hardening
4. A4 deploy-observability preset
5. A5 complete example app
6. B1 companion-aware operator surface
7. B2 companion lifecycle UX
8. B3 quickstart and troubleshooting docs
9. C1 authenticated browse QA
10. C2 release-doc sync tuning
11. C3 release-readiness tightening
12. C4 review-pack evolution
13. D1 lane scoring
14. D2 candidate scoring
15. D3 lane-2 gate decision

## Bottom Line

The next stretch should make Forge harder, clearer, and more believable on real solo-dev work.

That means:
- use the current lane on real repos
- harden auth, billing, deployment, and QA
- improve operator clarity
- earn the right to open the second lane later
