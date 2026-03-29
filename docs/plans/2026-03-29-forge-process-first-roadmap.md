# Forge Process-First Roadmap

Date: 2026-03-29
Status: current
Input:
- `docs/PRODUCT_THESIS_2026-03-29.md`
- `docs/PROJECT_PHASE1_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE2_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE3_REPORT_2026-03-28.md`

## Goal

Make Forge dependable for a solo developer from brainstorm to product-ready shipping without binding the product identity to any one stack.

## Non-Goals

- do not turn one companion into the identity of Forge
- do not chase equal automation depth for every stack
- do not expand companion breadth before the universal workflow is sharp
- do not become a generic prompt warehouse

## Strategy Shift

Old direction:
- build deep around a committed companion lane and expand outward later

Current direction:
- make the universal shipping workflow excellent first
- let the user choose the stack
- use companions as optional enrichers, not as the center of gravity

## Product Shape

- `Forge Core`: orchestration, workflow contracts, evidence policy, brownfield onboarding, continuity, change artifacts, QA and release-state contracts
- `Forge Runtime Tools`: specialized runtime executors such as `forge-browse` and `forge-design`
- `Forge Companions`: optional stack packs chosen by the user or inferred from the repo
- `Forge Artifacts`: specs, plans, codebase maps, active changes, decisions, learnings, QA runs, and release reports

## Phase 1: Universal Workflow Hardening

**Intent:** make Forge universally useful before any stack-specific depth is considered critical.
**Why now:** this is the actual product identity.
**Window:** 2 to 4 weeks

### Outcomes

- brainstorm, spec, plan, build, test, review, QA, and release flow feel like one coherent system
- `doctor`, `map-codebase`, `help`, and `next` feel like first-class operator surfaces
- change artifacts and continuity become normal workflow state, not optional ceremony
- Forge is clearly helpful even when no companion is active

### Build Order

1. workflow unification
   Deliver: make the journey from brainstorm to ship more explicit in docs, workflow entrypoints, and state transitions.
   Verify: a user can follow one repo-visible path from intent to release-readiness without hidden jumps.
   Exit: Forge feels like one system instead of separate features.

2. brownfield operator polish
   Deliver: tighten `doctor`, `map-codebase`, `help`, `next`, and `dashboard` so they explain current repo state and next action clearly.
   Verify: a brownfield repo can be diagnosed and summarized without reading internals.
   Exit: joining an unfamiliar repo becomes a normal strength of Forge.

3. artifact and continuity polish
   Deliver: sharpen active change folders, archive behavior, decisions, learnings, and workflow-state visibility.
   Verify: long-running work can be resumed with durable context and clear evidence.
   Exit: important state no longer depends on remembering the chat.

4. universal quality and release contracts
   Deliver: tighten verify, review, release-doc sync, release readiness, and review pack as stack-agnostic contracts.
   Verify: missing evidence or drift is reported consistently even on repos without companions.
   Exit: shipping discipline is visible as a universal strength.

### Not In Phase 1

- new flagship companions
- stack-specific scaffolding breadth
- framework-specific deploy automation

### Exit Criteria

- Forge is useful on real repos with no companion active
- the universal workflow from brainstorm to release is understandable
- quality and release state are inspectable through artifacts

## Phase 2: Stack-Agnostic Shipping UX

**Intent:** improve the generic shipping experience without assuming a preferred framework.
**Why now:** once the workflow is coherent, operator ergonomics becomes the main multiplier.
**Window:** 3 to 5 weeks

### Outcomes

- users understand what Forge is assuming and what it is not
- QA and release surfaces are easier to run repeatedly
- stack choice becomes an explicit user-facing decision instead of an implicit repo bias

### Build Order

1. operator entry and quickstart refresh
   Deliver: one clear quickstart, one troubleshooting path, and one decision guide that explains core-only vs optional companion usage.
   Verify: docs checks confirm commands, files, and links exist.
   Exit: a new user can adopt Forge without reading internal strategy docs.

2. generic QA loop hardening
   Deliver: improve reusable QA packets, session-backed checks, and QA reporting without requiring one framework-specific flow.
   Verify: a sample private app flow and a sample public flow both run through the same QA surface.
   Exit: `forge-browse` becomes a normal solo-dev tool instead of a special-case extra.

3. release-state hardening
   Deliver: sharpen release-doc sync, release readiness, and review pack on generic repo signals first.
   Verify: real drift and missing-evidence cases are caught without assuming a companion pack.
   Exit: release surfaces become credible before stack-specific enrichment.

4. stack-choice assistance
   Deliver: add user-facing guidance for when a companion is useful, how stack inference works, and where Forge remains stack-agnostic.
   Verify: decision docs stay aligned with install or inspect behavior.
   Exit: users feel they choose the stack and optional enrichments, not the other way around.

### Not In Phase 2

- declaring a mandatory flagship lane
- large template catalogs
- companion-first marketing narrative

### Exit Criteria

- operator UX is strong without relying on a central stack
- QA and release-state surfaces are repeatable on multiple repo shapes
- companion usage is explicit, optional, and understandable

## Phase 3: Optional Adaptation Layer

**Intent:** keep extensibility, but make it clearly secondary to the universal workflow.
**Why now:** only after the generic workflow is already strong.
**Window:** 3 to 6 weeks

### Outcomes

- companions are easier to install, inspect, and trust
- stack-specific depth can be attached without polluting `forge-core`
- Forge supports user-chosen stacks better without turning into a framework zoo

### Build Order

1. companion contract cleanup
   Deliver: make companion boundaries, allowed injections, and reporting surfaces easier to understand.
   Verify: contract docs, install UX, and inspect output say the same thing.
   Exit: companions feel like clean optional modules.

2. companion lifecycle UX
   Deliver: improve install, inspect, compatibility, registration, and stale-entry handling.
   Verify: lifecycle integration tests cover normal and broken states.
   Exit: using a companion no longer feels expert-only.

3. reference companions
   Deliver: keep a small number of example companions, such as `nextjs-typescript-postgres`, to prove the contract.
   Verify: each reference companion still passes its bundle verification and does not leak stack assumptions into core.
   Exit: Forge proves adaptation is real without making one stack the product identity.

4. user-chosen stack enrichment
   Deliver: better detection, command hints, verification packs, and optional templates for stacks users actually bring.
   Verify: enrichments work as accelerators, and Forge remains useful when they are absent.
   Exit: the adaptation layer serves user choice instead of replacing it.

### Not In Phase 3

- first-class support claims for every stack
- deep framework automation everywhere
- making lane choice the headline product narrative

### Exit Criteria

- companions are clearly optional
- the repo stays honest about shipped vs partial stack support
- Forge is stronger with companions, but not dependent on them for basic value

## Sequencing Rules

1. Do not make a companion the center of product identity.
2. Do not add new stack packs before the generic workflow gets sharper.
3. Do not let stack-specific release logic weaken the universal evidence contract.
4. Every companion feature must have a clear "works without companion" fallback story.
5. Prefer real user stack pressure over speculative template expansion.

## Reference Companion Policy

`nextjs-typescript-postgres` remains useful as:
- a reference companion
- a contract test for the adaptation layer
- an optional accelerator for users who actually want that stack

It is not:
- the identity of Forge
- the required path for maturity
- proof that Forge should prefer Next.js over the user's chosen stack

## Exact Near-Term Order

1. sharpen the universal workflow narrative
2. harden brownfield operator surfaces
3. improve artifact and continuity visibility
4. tighten universal QA and release contracts
5. refresh quickstart and decision UX
6. improve generic QA loops
7. improve generic release-state UX
8. clean up companion lifecycle and reference-companion messaging

This order keeps Forge aligned with the actual product goal: a stack-agnostic solo-dev execution system with optional adaptation, not a framework centered on one stack.
