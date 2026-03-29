# Forge Solo-Dev Roadmap
**Status:** historical roadmap, superseded by `docs/PRODUCT_THESIS_2026-03-29.md` and `docs/plans/2026-03-29-forge-process-first-roadmap.md`
**Date:** 2026-03-28
**Input:** [2026-03-28-solo-dev-ecosystem-review.md](C:\Users\Admin\.gemini\forge\docs\audits\2026-03-28-solo-dev-ecosystem-review.md)
**Goal:** make Forge dependable for one solo dev from brainstorm to product-ready shipping
**Non-goal:** do not chase equal support for every stack, do not become a generic skill warehouse, do not add content-marketing scope

Current policy note:
- one first-party companion lane is committed today: `nextjs-typescript-postgres`
- lane 2 is candidate-only until lane 1 is hardened and a separate product-pull decision is made
- governance artifacts beyond `docs/`, `docs/plans/`, `docs/specs/`, and decisions or learnings are still planned, not shipped

## Product Shape
- `Forge Core`: orchestration, verification, adapters, runtime-tool boundaries
- `Forge Ops`: doctor, codebase mapping, continuity, QA, release, dashboard, canary
- `Forge Lanes`: first-party opinionated paths for selected product types
- `Forge Artifacts`: durable change folders, repo-visible planning artifacts, and decisions or learnings; protected intent docs and human-owned backlog surfaces remain planned
- Gate 1: Phase 2 starts only after Phase 1 is usable on real repos
- Gate 2: Phase 3 starts only after at least one lane works end to end
- Gate 3: no lane ships without verification plus an example path

## Phase 1: Solo-Dev Foundation
**Intent:** close the gap between a strong kernel and a usable solo-dev surface.
**Why now:** without diagnosis, brownfield onboarding, continuity, and a cleaner ship loop, Forge still feels like infrastructure.
**Window:** 2 to 4 weeks

### Outcomes
- Forge can diagnose install and runtime health.
- Forge can inspect an existing repo and emit structured project context.
- Forge can resume long-running work with less repetition.
- Medium and large work leaves durable change artifacts instead of disappearing into chat history.
- Forge can separate verified facts from assumptions in the ship loop.

### Build Order
1. `doctor`
   Deliver: operator surface for Python, Node or Bun, git, host wiring, runtime bundle registration, Playwright health, preferences state, workspace artifact sanity.
   Repo areas: `packages/forge-core/workflows/operator/doctor.md`, `packages/forge-core/scripts/doctor*.py`, host wrappers, tests.
   Verify: healthy repo passes; broken fixture returns actionable remediation; JSON output is stable.
   Exit: a new user can run `doctor` and understand what is broken without reading internals.
2. `map-codebase`
   Deliver: operator surface that writes `.forge-artifacts/codebase/` with stack, architecture, conventions, tests, integrations, risks, and open questions; supports partial focus like `api` or `auth`.
   Repo areas: `packages/forge-core/workflows/operator/map-codebase.md`, `packages/forge-core/scripts/map_codebase*.py`, brownfield fixtures.
   Verify: an existing sample repo can run `map-codebase`; rerun updates artifacts cleanly; `help` and `next` can consume the output.
   Exit: Forge can join an existing repo and explain what it is looking at before implementation starts.
3. continuity upgrade
   Deliver: formal memory layers for `session`, `continuity`, `decisions`, `learnings`; stronger capture and restore flow; shared read path for `help`, `next`, and future lanes.
   Repo areas: `packages/forge-core/scripts/capture_continuity.py`, `packages/forge-core/workflows/execution/session.md`, continuity docs, tests.
   Verify: restore works across separate sessions; decisions and learnings persist in stable schema; repeated handoff requires less manual restating.
   Exit: solo-dev work can resume with continuity instead of session amnesia.
4. change artifacts plus tighter verify and ship loop
   Deliver: per-change folders for medium and large work with proposal, design, tasks, and archive path; cleaner `verify`, `ship`, and `release-doc sync` flow; stronger `forge-browse` hooks; initial privacy and sensitive-operation guard with allow, warn, or block behavior.
   Repo areas: core execution workflows, artifact schemas, runtime-tool invocation boundaries, release helpers.
   Verify: the same verification method is used before and after change; docs-only flows use diff or content checks; archived change state updates durable project knowledge; reports separate proof from assumptions.
   Exit: Forge can plan, implement, verify, archive, and ship with less ambiguity about what was actually proven.

### Not In Phase 1
- broad stack presets
- heavy dashboard work
- advanced canary automation
- first-class support for many frameworks

### Exit Criteria
- install plus `doctor` is understandable
- brownfield repo mapping works
- continuity is useful in practice
- change artifacts survive after the chat window is gone
- Forge feels materially helpful before any first-party lane exists

## Phase 2: First-Party Companion Depth
**Intent:** stop being generic on the surface and go deep on one committed lane before investing in another.
**Why now:** after the foundation exists, depth is more valuable than more abstractions.
**Window:** 3 to 6 weeks

### Lane Choice
1. committed lane: `lane-nextjs-saas` = Next.js + TypeScript + Postgres
2. early candidate only: `lane-fastapi-api` = FastAPI + Postgres

### Outcomes
- `init` becomes preset-driven instead of minimal skeleton only.
- Forge can scaffold a real project spine in one committed lane.
- Forge gets one optimized product path without turning `forge-core` into a stack-specific framework.
- Governance artifacts beyond the current docs or plans scaffolding are tracked as follow-up work, not counted as Phase 2 proof.
- Forge gets first-class depth somewhere instead of weak breadth everywhere.

### Build Order
1. preset-aware `init`
   Deliver: lane selection or inference; generated project spine with docs structure, planning state, lane metadata, verification defaults, and deploy assumptions. Protected product-intent docs, document ownership rules, and human-owned backlog conventions are follow-up governance work, not Phase 2 completion criteria.
   Repo areas: `packages/forge-core/references/workspace-init.md`, `packages/forge-core/scripts/initialize_workspace.py`, lane registry, tests.
   Verify: each lane initializes from scratch; generated artifacts are consistent; lane defaults are visible to later workflows.
   Exit: `init` becomes the first real step of a product path, not just a skeleton dump.
2. lane metadata and stack set
   Deliver: one source of truth per lane for snippets, commands, conventions, risk notes, and migration notes.
   Repo areas: lane data in `packages/forge-core/data/`, lane references in `packages/forge-core/references/`, route tests.
   Verify: lane metadata resolves deterministically; workflows can read lane-specific commands without ad-hoc branching.
   Exit: Forge can reason about a lane from declared metadata instead of brittle heuristics.
3. starter templates
   Deliver: `lane-nextjs-saas` gets auth shell, layout shell, database wiring, testing baseline, deploy baseline. Lane 2 remains candidate-only until the lane expansion rule is satisfied.
   Repo areas: starter template packages or fixtures, init wiring, docs.
   Verify: templates boot locally, pass default verify flow, and absorb small feature work without immediate restructuring.
   Exit: a solo dev can start from a real template instead of assembling their own base stack.
4. lane verification packs
   Deliver: lane-specific checklists and scripts with strong defaults for lint, typecheck, tests, migration safety, and env validation.
   Repo areas: workflow verification profiles, lane scripts, fixtures.
   Verify: seeded lane-specific failures are caught in fixtures.
   Exit: quality does not collapse back into generic verification.
5. lane docs and example repos
   Deliver: one example repo for the committed lane, one quickstart for that lane, and one "ship a v1" walkthrough. Lane-2 docs stay exploratory until the expansion rule is explicitly passed.
   Repo areas: docs, examples, release checks.
   Verify: each example repo passes verify; docs and examples stay in sync; each lane has one end-to-end path from brainstorm to ship.
   Exit: lanes become repeatable product paths instead of theory.

### Not In Phase 2
- a third lane
- mobile first-class support
- Go, .NET, or Java first-class support
- a giant template matrix

### Exit Criteria
- at least one solo dev can start a product in one committed lane without assembling a custom process
- `init` no longer feels generic
- Forge has first-class support somewhere, not weak support everywhere

## Phase 3: Product-Ready Shipping Intelligence
**Intent:** make Forge trustworthy for shipping and operating a real product.
**Why now:** advanced shipping intelligence matters only after foundation and lanes are already real.
**Window:** 3 to 5 weeks

### Outcomes
- richer browser QA and release checks
- release-doc and deploy-state verification
- useful dashboard for long-running work
- light canary and release-readiness flow for selected lanes

### Build Order
1. `dashboard`
   Deliver: terminal-first status view for active work slice, latest plan, latest verification, continuity state, pending risks, and runtime tool health.
   Repo areas: operator workflow, file-backed state, continuity readers.
   Verify: dashboard reflects a real sample repo without manual editing.
   Exit: one solo dev can see work state without digging through artifacts manually.
2. stronger `forge-browse` QA
   Deliver: persistent authenticated sessions, easier snapshot and assert loop, reusable QA packets for lane flows.
   Repo areas: `forge-browse`, verification workflows, example repos.
   Verify: authenticated path works on a sample app; QA packets feed release flow cleanly.
   Exit: browser verification becomes normal product work instead of an exotic add-on.
3. release-doc sync
   Deliver: docs drift checks after shipping; update guidance for README, architecture, release notes, and related surfaces; explicit report of what changed and what still needs judgment.
   Repo areas: release helpers, docs checks, ship workflows.
   Verify: seeded drift in an example repo is detected and reported correctly.
   Exit: product shipping no longer drifts silently away from docs and state.
4. canary and release readiness
   Deliver: thin readiness gates for selected lanes, post-deploy health and smoke checks, optional benchmark hooks where they add signal.
   Repo areas: canary scripts, release checks, lane fixtures.
   Verify: fixture canary catches at least one intentionally broken deploy condition.
   Exit: Forge adds lightweight but real post-deploy confidence.
5. solo-dev review pack
   Deliver: optional adversarial review mode, security-minded review for public-facing apps, lane-aware release checklist.
   Repo areas: review workflows, lane release docs, fixtures.
   Verify: review pack catches at least one seeded security or release risk in fixtures.
   Exit: pre-release review becomes a repeatable product surface, not an ad-hoc ritual.

### Not In Phase 3
- enterprise observability platform
- complex SRE stack
- multi-service fleet management
- full security suite beyond focused release gates

### Exit Criteria
- Forge is trustworthy enough to help a solo dev ship and check a live product
- product state, QA state, and release state are visible and testable

## Global Sequencing Rules
1. Do not start lane 3 before lanes 1 and 2 are clean.
2. Do not build advanced release intelligence before `doctor` and `map-codebase`.
3. Do not add more host-specific UX until the solo-dev surface is stronger.
4. Every lane and ops feature needs verification plus at least one example path.

## Exact Build Order
1. `doctor`
2. `map-codebase`
3. continuity upgrade
4. change artifacts plus tighter verify and ship loop
5. preset-aware `init`
6. lane metadata and stack set
7. starter templates for two lanes
8. lane verification packs
9. lane docs and example repos
10. `dashboard`
11. stronger `forge-browse` QA
12. release-doc sync
13. canary and release readiness
14. solo-dev review pack

This order forces Forge to become useful on real solo-dev work before it expands again.
