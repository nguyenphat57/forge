# Forge Process-First Implementation Plan

Date: 2026-03-29
Status: current implementation plan
Inputs:
- `docs/PRODUCT_THESIS_2026-03-29.md`
- `docs/plans/2026-03-29-forge-process-first-roadmap.md`
- `docs/PROJECT_PHASE1_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE2_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE3_REPORT_2026-03-28.md`

## Qualified Problem Statement

For:
- a solo developer shipping in a real repo

Who:
- needs a dependable workflow that stays useful across stacks and across sessions

That:
- turns rough intent into reviewable plans, brownfield diagnosis, visible QA and release state, and optional stack enrichment without making one companion the product identity

## Goal

Translate the current process-first thesis into a concrete build order across `forge-core`, runtime tools, host adapters, and the reference companion.

## Success Signals

- `forge-core` is clearly useful on repos with no companion active
- brownfield operator surfaces explain repo state and next action with repo-visible artifacts
- QA and release surfaces catch missing evidence on generic repos before companion-specific enrichment
- runtime tools stay clearly separated from core orchestration
- `nextjs-typescript-postgres` remains a reference companion instead of the implied center of product identity

## Source Of Truth

- product identity and policy: `docs/PRODUCT_THESIS_2026-03-29.md`
- sequencing: `docs/plans/2026-03-29-forge-process-first-roadmap.md`
- implementation evidence: package tests, repo verification, and release docs

## Scope In

- docs and operator wording that still imply a stack-centered identity
- `forge-core` brownfield, operator, artifact, QA, and release surfaces
- runtime-tool boundary clarity for `forge-browse` and `forge-design`
- host-adapter messaging that companions are optional
- reference-companion contract and lifecycle clarity

## Scope Out

- new flagship companions
- large template catalogs
- deep stack-specific deploy automation outside the reference companion
- claims of equal first-class support across many stacks
- marketing-site or branding work outside repo delivery docs

## File Or Surface Map

- core policy docs under `docs/`
- `packages/forge-core/SKILL.md`
- `packages/forge-core/workflows/operator/{doctor,map-codebase,help,next,dashboard}.md`
- `packages/forge-core/workflows/execution/{change,release-doc-sync,release-readiness}.md`
- `packages/forge-core/scripts/{doctor*.py,map_codebase*.py,resolve_help_next.py,dashboard*.py,capture_continuity.py,change_artifacts*.py,release_doc_sync.py,release_readiness.py,review_pack.py}`
- `packages/forge-core/tests/{test_doctor.py,test_map_codebase.py,test_help_next.py,test_help_next_workflow_state.py,test_dashboard.py,test_change_artifacts.py,test_release_doc_sync.py,test_release_readiness.py,test_review_pack.py,test_workspace_canary.py,test_canary_rollout.py}`
- `packages/forge-browse/*` and `packages/forge-design/*`
- `packages/forge-codex/overlay/*` and `packages/forge-antigravity/overlay/*`
- `packages/forge-nextjs-typescript-postgres/{README.md,SKILL.md,companion.json,data/,scripts/,tests/}`
- `scripts/verify_repo.py`

## Spec-Review Requirement

- not required for doc-only alignment or wording cleanup
- required before changing public artifact schemas, companion injection contracts, release verdict contracts, or install/register lifecycle behavior

## Implementation-Ready Packet

- Sources: thesis, roadmap, phase reports, and the current package tests
- Slice 1: workflow identity alignment | Boundary: current docs plus core and host operator wording | Proof: content checks plus `python scripts/verify_repo.py`
- Slice 2: brownfield operator hardening | Boundary: `doctor`, `map-codebase`, `help`, `next`, and `dashboard` | Proof: targeted `pytest` for those surfaces
- Slice 3: artifact and continuity polish | Boundary: change artifacts, archive-back flow, and decisions or learnings capture | Proof: targeted `pytest` plus fixture diff review
- Slice 4: universal QA and release contract hardening | Boundary: review pack, release-doc sync, release readiness, workspace canary, and rollout reporting | Proof: targeted `pytest` for release and canary surfaces
- Slice 5: stack-agnostic shipping UX | Boundary: quickstart, troubleshooting, decision guidance, and runtime-tool docs | Proof: docs checks plus `python scripts/verify_repo.py`
- Slice 6: optional adaptation-layer cleanup | Boundary: companion contract, install or inspect UX, and reference-companion messaging | Proof: companion contract tests plus core fallback checks
- Dependencies and order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
- Reopen only if: core-only flow is still not useful enough, runtime-tool boundaries need to change, or companion work requires a public contract change

## Phase 1: Universal Workflow Hardening

### 1. Workflow Identity Alignment

Deliver:
- audit current docs and operator surfaces for stack-centered language
- replace that wording with process-first, stack-agnostic language wherever current policy should speak

Verify:
- content checks for `stack-agnostic`, `user chooses the stack`, and `companions are optional` where applicable
- `python scripts/verify_repo.py`

Exit:
- current policy docs and operator entry surfaces tell one story

### 2. Brownfield Operator Polish

Deliver:
- make `doctor`, `map-codebase`, `help`, `next`, and `dashboard` the default front door for an unfamiliar repo
- remove any unnecessary companion-first assumptions from summaries or next-step guidance

Verify:
- `python -m pytest packages/forge-core/tests/test_doctor.py packages/forge-core/tests/test_map_codebase.py packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_help_next_workflow_state.py packages/forge-core/tests/test_dashboard.py`

Exit:
- a brownfield repo can be diagnosed and handed a clear next step without companion assumptions

### 3. Artifact And Continuity Polish

Deliver:
- tighten change-artifact defaults, archive-back rules, and decisions or learnings capture
- make long-running work easier to resume from repo-visible state

Verify:
- `python -m pytest packages/forge-core/tests/test_change_artifacts.py`

Exit:
- active work state is durable and resume-friendly

### 4. Universal Quality And Release Contract Hardening

Deliver:
- sharpen `review_pack`, `release_doc_sync`, `release_readiness`, workspace canary, and rollout reporting as stack-agnostic contracts

Verify:
- `python -m pytest packages/forge-core/tests/test_review_pack.py packages/forge-core/tests/test_release_doc_sync.py packages/forge-core/tests/test_release_readiness.py packages/forge-core/tests/test_workspace_canary.py packages/forge-core/tests/test_canary_rollout.py`

Exit:
- missing evidence or doc drift is caught consistently on repos with no companion

## Phase 2: Stack-Agnostic Shipping UX

### 1. Quickstart And Decision Refresh

Deliver:
- one clear quickstart
- one troubleshooting path
- one core-only versus companion decision guide

Verify:
- docs link and content checks
- `python scripts/verify_repo.py`

Exit:
- a new user can start without reading internal strategy material

### 2. Generic QA Loop Hardening

Deliver:
- make `forge-browse` the reusable QA executor for both public and authenticated flows without implying one framework

Verify:
- `python -m pytest packages/forge-browse/tests/test_browse_contracts.py packages/forge-browse/tests/test_browse_packets.py packages/forge-browse/tests/test_browse_runtime.py packages/forge-browse/tests/test_playwright_cli.py`

Exit:
- browser QA feels like a normal Forge surface instead of a sidecar experiment

### 3. Design And Runtime Boundary Clarity

Deliver:
- keep `forge-design` focused on design artifacts and `forge-browse` focused on runtime QA
- align docs and host wrappers with that split

Verify:
- `python -m pytest packages/forge-design/tests/test_design_contracts.py packages/forge-design/tests/test_design_packet.py packages/forge-design/tests/test_forge_design_cli.py packages/forge-browse/tests/test_browse_runtime.py`

Exit:
- runtime-tool boundaries are explicit and non-overlapping

### 4. Release-State UX Hardening

Deliver:
- improve release-state reporting and operator guidance without requiring companion-specific enrichment

Verify:
- rerun the Phase 1 release suite
- `python scripts/verify_repo.py`

Exit:
- release surfaces are credible before adaptation-layer depth

## Phase 3: Optional Adaptation Layer

### 1. Companion Contract Cleanup

Deliver:
- make allowed companion enrichments, fallback behavior, and reporting boundaries explicit

Verify:
- `python -m pytest packages/forge-nextjs-typescript-postgres/tests/test_contracts.py packages/forge-nextjs-typescript-postgres/tests/test_command_profiles.py`

Exit:
- companions read as optional modules, not product identity

### 2. Companion Lifecycle UX

Deliver:
- harden install, inspect, compatibility, and stale-entry handling for optional companions

Verify:
- companion lifecycle or contract tests for the touched surfaces
- `python scripts/verify_repo.py`

Exit:
- using a companion is routine and inspectable

### 3. Reference Companion Cleanup

Deliver:
- keep `nextjs-typescript-postgres` as a reference companion that proves the contract without leaking stack assumptions into core

Verify:
- `python -m pytest packages/forge-nextjs-typescript-postgres/tests/test_doctor_and_map.py packages/forge-nextjs-typescript-postgres/tests/test_init_preset.py`

Exit:
- the reference companion stays strong while remaining clearly optional

## Near-Term Build Order

1. align current docs and operator wording with the new thesis
2. harden brownfield operator surfaces in `forge-core`
3. tighten artifact and continuity behavior
4. harden universal QA and release contracts
5. refresh quickstart and decision UX
6. clarify `forge-browse` and `forge-design` boundaries
7. clean up companion contract and lifecycle
8. re-verify that core-only flow remains useful without a companion

## Risks And Assumptions

- Risk: older docs or operator references continue to imply a favored stack
  Mitigation: start with a wording and policy audit before deeper implementation work
- Risk: release or QA surfaces secretly depend on companion-only assumptions
  Mitigation: require at least one core-only verification path for every new release or QA surface
- Risk: runtime tools drift into core responsibilities
  Mitigation: keep separate verification for `forge-browse` and `forge-design`
- Assumption: the existing phase-report assets are strong enough that Forge needs strategic refocus more than a technical reset
- Assumption: `nextjs-typescript-postgres` remains the only reference companion in the near term

## Verification Strategy

- doc-only or wording slices: targeted content checks plus `git diff --stat` plus `python scripts/verify_repo.py`
- core operator slices: targeted `pytest` suites for touched surfaces
- runtime-tool slices: package-local `pytest` suites
- companion slices: package-local contract or enrichment tests plus core fallback checks
- release before claim: rerun the exact proof named for each completed slice and report any residual gap explicitly
