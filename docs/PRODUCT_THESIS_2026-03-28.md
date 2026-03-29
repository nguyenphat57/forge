# Forge Product Thesis

Date: 2026-03-28
Status: proposed
Inputs:
- `docs/plans/2026-03-28-forge-solo-dev-roadmap.md`
- `docs/PROJECT_PHASE1_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE2_DEEPENING_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE3_REPORT_2026-03-28.md`

## Thesis

Forge should become the most dependable assistant for a solo developer who needs to move from idea to product-ready shipping in a real repo.

Forge is not a monolithic framework and not a generic skill warehouse. It is an orchestrator kernel with strong shipping discipline, durable artifacts, runtime-tool boundaries, and first-party companions that provide optimized product paths for selected stacks.

## User And Problem

Primary user:
- one solo developer shipping a real product with limited time and limited operational support

Core problem:
- solo developers do not only need code generation
- they need help with diagnosis, planning, repo onboarding, continuity, verification, QA, release checks, and product-state visibility
- most AI tooling is either too generic to trust or too opinionated to adapt to the repo that already exists

Forge should solve this by helping a solo developer:
- join an existing repo fast
- keep state outside chat
- make changes with evidence before claims
- run repeatable QA and release checks
- use stack-specific depth through companions without turning the core into a stack-specific framework

## Product Shape

### 1. Forge Core

`forge-core` is the orchestrator kernel.

It owns:
- routing and workflow selection
- quality gates and evidence rules
- doctor, map-codebase, continuity, and change artifacts
- release readiness, release-doc sync, review pack, and dashboard contracts
- runtime-tool boundaries and reporting contracts

It does not own:
- stack-specific app conventions
- framework-specific project scaffolds
- product-shape assumptions such as Next.js routing or Vercel deployment

### 2. First-Party Companions

Companions provide optimized product paths for selected stacks.

They may contribute:
- stack detection hints
- init presets and templates
- doctor enrichers
- map-codebase enrichers
- command profiles
- verification packs
- risk notes and lane-aware review hints

They must not replace:
- core routing
- core evidence policy
- core workflow-state contracts
- core release verdict logic

### 3. Runtime Tools

Runtime tools stay separate from the kernel.

Current pattern:
- `forge-browse` handles browser-side QA surfaces
- `forge-design` handles design-side surfaces

This keeps the kernel focused on orchestration while still allowing deeper execution support where it matters.

### 4. Durable Artifacts

Forge should prefer repo-visible state over chat-only state.

Important artifact classes:
- codebase maps
- active change folders
- decisions and learnings
- verification reports
- release-doc sync reports
- release-readiness reports
- QA packet definitions and runs

## Product Principles

### Evidence Before Claims

Forge should not claim completion without fresh proof. This is the main trust mechanism for solo-dev shipping.

### Brownfield First

Forge must work on repos that already exist. Greenfield scaffolding matters, but repo onboarding is the first product surface.

### Core Stays Lane-Agnostic

Golden paths live in companions. The core stays generic enough to serve multiple product shapes later.

### Depth Beats Breadth

Forge should become excellent on a very small number of product paths before opening more lanes.

### Operator-Visible State

A solo developer should be able to inspect project state, QA state, release state, and active risk without reading internal implementation details.

### Human Ownership Where It Matters

Protected product intent, decisions, and backlog surfaces should stay legible and reviewable by the developer, not be buried inside generated output.

## What Forge Is Not

Forge is not:
- a replacement for product judgment
- a universal framework with equal depth for every stack
- a multi-agent spectacle optimized for theater over delivery
- a generic prompt collection with no operational surface
- an enterprise platform for large-team workflow management

## Proof After Three Phases

After the completed Phase 1 to Phase 3 work, Forge already has credible building blocks for this thesis:

- Phase 1 made the core useful on real repos through `doctor`, `map-codebase`, continuity, and change artifacts.
- Phase 2 proved the companion model by keeping `forge-core` generic while moving `nextjs-typescript-postgres` depth into a first-party companion.
- Phase 3 added shipping intelligence through `dashboard`, reusable QA packets, release-doc sync, release readiness, and review pack surfaces.

This means Forge now has more than an orchestration story. It has a repo-visible shipping system.

## Current Golden Path

Today the first optimized path is:
- `nextjs-typescript-postgres`

This path should be treated as the reference companion, not as the identity of Forge.

Forge identity:
- dependable assistant for solo developers shipping real products

Current optimized path:
- a first-party companion for one web-product lane

## Strategy For The Next Stretch

The next stretch should not be about more abstractions and not about opening many lanes.

It should be about:
- hardening the first companion on real repos
- improving operator UX around companion install, diagnosis, and release confidence
- proving that Forge materially reduces friction on actual solo-dev shipping work

## Lane Expansion Rule

Forge should open a second first-party lane only when all of the following are true:

- the first companion is used on at least one real product repo
- the example path is complete enough to ship a meaningful v1
- verification packs catch real seeded failures
- release and QA surfaces are used as part of normal work, not demo-only work
- the new lane has a stronger product pull than more hardening on the existing lane

Until then, breadth should remain companion-friendly in architecture but intentionally narrow in first-party investment.

## Success Signals

Forge is on the right path when:
- a solo developer can join a brownfield repo and get usable diagnosis fast
- active work survives across sessions through durable artifacts
- verification and release state are inspectable instead of implied
- the first companion can start and support a product without immediate custom process assembly
- real-repo usage produces fewer repeated operator questions over time

## Bottom Line

Forge should be developed as:
- an orchestrator kernel in `forge-core`
- a set of first-party companions for optimized product paths
- a repo-visible shipping system for solo developers

That keeps the concept broad enough to stay useful across projects while keeping execution narrow enough to become trustworthy.
