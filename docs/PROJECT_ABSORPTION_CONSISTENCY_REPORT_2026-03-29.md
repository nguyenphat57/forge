# Forge Absorption Consistency Report

Date: 2026-03-29
Status: current
Goal: normalize the repo narrative after the roadmap, thesis, and multi-phase delivery reports diverged on lane policy, governance artifacts, and risk-guard scope.

## Scope

This report is the repo-visible answer to one question:

Have the external-review absorption points now been described consistently across audit, roadmap, thesis, backlog, and delivery reports?

## Canonical Decisions

### 1. Lane policy

Canonical rule:
- Forge has one committed first-party companion lane today: `nextjs-typescript-postgres`
- lane 2 is candidate-only until the lane gate passes and product pull is explicitly confirmed

Why:
- earlier audit and roadmap wording explored two first-party lanes too early
- later thesis and real-repo evidence made it clear that lane 1 should be hardened first

Repo effect:
- the thesis is the canonical policy document
- the roadmap now marks the two-lane wording as historical
- `lane_gate.py` now requires explicit product-pull confirmation instead of treating evidence alone as automatic approval

### 2. Governance artifacts

Canonical rule:
- shipped today: `docs/`, `docs/plans/`, `docs/specs/`, change artifacts, and durable `decisions` or `learnings`
- not yet shipped as completed absorption: protected product-intent docs, document ownership rules, and human-owned backlog conventions

Why:
- the external review identified these as valuable
- the implementation reports did not provide strong repo evidence for them yet

Repo effect:
- roadmap and thesis now describe them as planned follow-up work instead of completed depth
- backlog now includes explicit governance-artifact work

### 3. Risk or privacy guard absorption

Canonical rule:
- shipped today: an initial risk guard through `change_guard` with `allow`, `warn`, and `block`
- not yet shipped: a deep privacy mesh or policy engine

Why:
- the audit chose privacy or risk guard behavior as a useful absorption
- the actual implementation is meaningful, but intentionally narrower than the full external concept

Repo effect:
- thesis now calls this a foundational safety rail, not a mature product pillar
- backlog now includes a step to deepen or explicitly retain this as partial

## Absorption Status

Fully absorbed and now described consistently:
- brownfield onboarding through `doctor` and `map-codebase`
- durable change artifacts with archive-back into decisions or learnings
- companion-based golden path architecture
- dashboard, QA packets, release-doc sync, release readiness, and review pack
- evidence-before-claims as the main trust contract

Partially absorbed and now described consistently as partial:
- governance artifacts beyond current planning scaffolds
- privacy or risk guard behavior beyond the initial `change_guard`
- searchable project intelligence beyond current decisions or learnings artifacts

Deferred by explicit policy:
- a second first-party lane

## Files Updated In This Normalization Pass

- `docs/audits/2026-03-28-solo-dev-ecosystem-review.md`
- `docs/plans/2026-03-28-forge-solo-dev-roadmap.md`
- `docs/PRODUCT_THESIS_2026-03-28.md`
- `docs/plans/2026-03-28-post-phase3-implementation-backlog.md`
- `docs/PROJECT_REAL_REPO_CANARY_AND_AUTH_QA_REPORT_2026-03-29.md`
- `packages/forge-core/scripts/lane_gate.py`
- `packages/forge-core/tests/test_lane_decision.py`

## Verdict

Yes, the repo is now materially more consistent.

More precisely:
- the core architecture story is consistent
- the lane-expansion policy is now consistent
- the governance and risk-guard absorptions are now consistent because they are labeled as partial or planned instead of being overclaimed

Remaining limitation:
- consistency is now good at the policy and report layer, but some planned absorptions still need implementation before they can move from "planned" to "shipped"
