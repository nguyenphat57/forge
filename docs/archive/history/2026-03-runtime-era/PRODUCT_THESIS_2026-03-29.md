# Forge Product Thesis

Date: 2026-03-29
Status: current policy baseline
Inputs:
- `docs/PRODUCT_THESIS_2026-03-28.md`
- `docs/archive/plans/2026-03-29-forge-process-first-roadmap.md`
- `docs/PROJECT_PHASE1_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE2_REPORT_2026-03-28.md`
- `docs/PROJECT_PHASE3_REPORT_2026-03-28.md`

## Thesis

Forge should become the most dependable stack-agnostic execution system for a solo developer who needs to go from brainstorm to product-ready shipping in a real repo.

Forge is not a monolithic framework and not a stack-specific starter kit.
It is a process-first orchestrator with strong shipping discipline, repo-visible artifacts, runtime-tool boundaries, and optional companions that adapt the workflow to the stack the user chooses.

When older roadmap or thesis wording differs, this document is the canonical policy.

## Forge Is

Forge is:
- a solo-dev execution system
- a stack-agnostic orchestration kernel
- a repo-visible shipping workflow
- a brownfield-first assistant, not only a greenfield scaffold tool
- a system that values evidence, state, and verification over chat fluency

## Forge Is Not

Forge is not:
- a universal framework with equal stack depth everywhere
- a product generator that chooses the user's stack for them
- a companion-first system whose value collapses without stack packs
- a prompt collection with no durable state
- a multi-agent spectacle optimized for theater over delivery

## User And Problem

Primary user:
- one solo developer shipping a real product with limited time and limited operational support

Core problem:
- solo developers do not only need code generation
- they need help with thinking, scoping, repo onboarding, continuity, verification, QA, release checks, and product-state visibility
- their stack may vary by project, and the tool should not become useless just because the stack changed

Forge should solve this by helping a solo developer:
- clarify what they are trying to build
- turn vague ideas into reviewable specs and plans
- join an existing repo fast
- keep state outside chat
- make changes with evidence before claims
- run repeatable QA and release checks
- optionally attach stack-specific help without requiring a central blessed stack

## Product Shape

### 1. Forge Core

`forge-core` is the orchestrator kernel.

It owns:
- routing and workflow selection
- brainstorm, spec, planning, build, debug, test, review, QA, and release workflow contracts
- quality gates and evidence rules
- doctor, map-codebase, continuity, and change artifacts
- release readiness, release-doc sync, review pack, and dashboard contracts
- runtime-tool boundaries and reporting contracts

It does not own:
- stack-specific app conventions
- framework-specific project scaffolds
- product-shape assumptions such as Next.js routing or Vercel deployment
- decisions about which stack a solo developer should use

### 2. Runtime Tools

Runtime tools stay separate from the kernel.

Current pattern:
- `forge-browse` handles browser-side QA surfaces
- `forge-design` handles design-side surfaces

This keeps the kernel focused on orchestration while still allowing deeper execution support where it matters.

### 3. Companions

Companions are optional stack packs, not the center of product identity.

They may contribute:
- stack detection hints
- doctor or map-codebase enrichers
- command profiles
- verification packs
- templates or presets
- stack-specific risk notes

They must not replace:
- core routing
- core evidence policy
- core workflow-state contracts
- core release verdict logic

Policy:
- the user chooses the stack
- Forge stays useful without any companion
- a companion is an accelerator, not a prerequisite

### 4. Durable Artifacts

Forge should prefer repo-visible state over chat-only state.

Important artifact classes:
- specs and plans
- codebase maps
- active change folders
- decisions and learnings
- verification reports
- QA packet definitions and runs
- release-doc sync reports
- release-readiness reports

## Product Principles

### Process First

Forge should win first by making the delivery process reliable across many repos, not by going deepest on one framework.

### User Chooses The Stack

Forge can help detect, explain, and enrich a stack, but it should not force a central stack strategy on the user.

### Brownfield First

Forge must work on repos that already exist.
Greenfield scaffolding matters, but repo onboarding is the first product surface.

### Evidence Before Claims

Forge should not claim completion without fresh proof.
This is the main trust mechanism for solo-dev shipping.

### Repo-Visible State

Important work should survive outside the chat window.

### Optional Depth, Not Mandatory Lane Dependence

Companions are useful, but Forge should still feel valuable when no companion is active.

## Strategy Shift

The previous strategy treated a first-party companion lane as the main center of gravity.

The current strategy is different:
- the center of gravity is the universal shipping workflow
- companions are optional adaptation layers
- a reference companion can still exist, but it is not the identity of Forge

Implication:
- `nextjs-typescript-postgres` is now a reference companion, not the north-star product thesis

## What Forge Should Optimize Now

Forge should become excellent at:
- turning rough intent into a clear next action
- enforcing evidence-before-claims
- explaining unfamiliar repos through `doctor` and `map-codebase`
- keeping plans, changes, QA, and release state visible
- helping a solo developer finish, not only start

Forge should not optimize first for:
- one framework's conventions
- template breadth
- deep stack-specific automation before the generic workflow is sharp

## Current Assets From Existing Work

The repo already contains strong building blocks for this direction:
- Phase 1 created the brownfield and artifact foundation through `doctor`, `map-codebase`, continuity, and change artifacts
- Phase 2 proved the companion model can stay outside the core
- Phase 3 created shipping-state surfaces through dashboard, QA packets, release-doc sync, release readiness, and review pack

This means Forge does not need a strategic reset at the implementation level.
It needs a strategic refocus at the product-policy level.

## Success Signals

Forge is on the right path when:
- a solo developer can join a brownfield repo and get useful diagnosis fast
- active work survives across sessions through durable artifacts
- QA and release state are inspectable instead of implied
- the workflow still feels helpful when no companion is active
- a user can choose a stack without feeling pushed toward a built-in favorite

## Bottom Line

Forge should be developed as:
- an orchestrator kernel in `forge-core`
- a stack-agnostic execution system for solo developers
- a repo-visible shipping workflow from brainstorm to product-ready
- a platform that offers optional companions without becoming dependent on them

That keeps Forge broad enough to support many kinds of solo-dev work while keeping the real differentiator where it belongs: process quality and shipping discipline.
