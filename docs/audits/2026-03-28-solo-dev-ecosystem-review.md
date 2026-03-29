# Forge Solo-Dev Ecosystem Review

Date: 2026-03-28
Reviewer: Codex
Goal: review external repos as input for shaping Forge into a solo-dev assistant that helps ship real products from brainstorm to product-ready.
Status note: this audit is landscape input, not the current product policy. Later repo decisions narrowed first-party investment to one committed companion lane first; lane 2 remains a candidate chosen by evidence plus product pull, not by this audit alone.

## Scope And Method

Source basis:
- official GitHub README content
- top-level repo structure
- visible command surface, workflows, docs, and installer story

Repos reviewed:
- [garrytan/gstack](https://github.com/garrytan/gstack)
- [obra/superpowers](https://github.com/obra/superpowers)
- [tody-agent/codymaster](https://github.com/tody-agent/codymaster)
- [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
- [vudovn/antigravity-kit](https://github.com/vudovn/antigravity-kit)
- [first-fluke/oh-my-agent](https://github.com/first-fluke/oh-my-agent)
- [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)
- [rune-kit/rune](https://github.com/rune-kit/rune)
- [josipjelic/orchestrated-project-template](https://github.com/josipjelic/orchestrated-project-template)

Review lens:
- Does this help a solo dev move from idea to shipped product?
- Is the value in orchestration, memory, presets, runtime tooling, or workflow discipline?
- What should Forge absorb directly, adapt carefully, or avoid?

## Executive Summary

Forge already has a strong orchestration kernel, verification discipline, host adapter architecture, and runtime-tool split. What it still lacks is a sharper product surface for solo-dev shipping.

The nine repos point to five gaps Forge should close:
- brownfield onboarding and codebase mapping
- continuity and project memory that compound over time
- lane-specific presets and starter templates
- spec and release artifacts that stay in sync with shipped work
- operator ergonomics such as doctor, dashboard, QA, and release readiness

The right direction is:

`Forge = execution platform core + opinionated solo-dev lanes + first-party shipping ops`

## High-Level Comparison

| Repo | Core Identity | Strongest Value | Best Absorption For Forge |
|---|---|---|---|
| gstack | Solo software factory | idea-to-ship loop, browser QA, release ops | shipping rituals, browser QA, docs sync |
| superpowers | Discipline-first skill system | hard process guardrails, TDD, evidence | verification rigor, worktree discipline |
| codymaster | AI operating system | memory architecture, continuity, dashboard | continuity tiers, learnings, decisions |
| get-shit-done | Pragmatic spec-driven system | project state, brownfield mapping, validation contract | map-codebase, health, requirement-to-verification |
| antigravity-kit | Template-heavy starter kit | stack presets and starter utility | first-party templates and app-builder presets |
| oh-my-agent | Portable multi-agent harness | `.agents` SSOT, doctor, dashboard, stack-set | source-of-truth model, presets, doctor |
| OpenSpec | Spec-driven development framework | fluid artifact-guided change workflow | change artifacts, archive loop, brownfield spec layer |
| rune | Mesh skill ecosystem | interconnected skills, compiler, privacy guard | compile-time routing, pack model, privacy guard |
| orchestrated-project-template | Claude project template | onboarding, living docs, PRD and backlog governance | onboarding flow, doc ownership, human-owned backlog |

## 1. gstack

Identity:
- the most productized idea-to-ship system in the set
- combines specialist flows, browser runtime, review, deploy, canary, and docs update

Strengths:
- strongest end-to-end shipping narrative: plan, build, review, QA, ship, benchmark, canary, retro
- browser capability is treated as real runtime infrastructure, not a loose suggestion
- release-minded commands such as QA, ship, land-and-deploy, document-release, canary, and benchmark
- safety controls like guard and freeze are useful patterns for risky work

Forge should absorb:
- a sharper ship loop with browser QA and release-doc sync
- stronger `forge-browse` ergonomics for persistent authenticated QA
- lightweight deploy verification, canary, and benchmark surfaces

Forge should avoid:
- AI org-chart theater
- too many overlapping commands
- charisma-heavy product claims that exceed what the tool can prove

## 2. superpowers

Identity:
- the cleanest discipline-first workflow system in the set
- optimized for process quality more than product breadth

Strengths:
- hard guardrails around planning, skill selection, TDD, worktrees, and verification-before-completion
- unusually concrete planning quality with exact paths, commands, and expected outputs
- strong separation between spec review and code-quality review

Forge should absorb:
- stronger evidence-before-claims discipline
- worktree-based isolation for medium and large work
- two-stage review: spec compliance first, code quality second

Forge should avoid:
- absolutist tone everywhere
- universal TDD enforcement for every context
- too much ceremony for small tasks

## 3. codymaster

Identity:
- an integrated AI operating system with skills, memory, dashboard, docs, and code intelligence

Strengths:
- strongest memory thesis in the set
- clear layered model for session memory, continuity, reinforced decisions and learnings, semantic search, and structural code memory
- dashboard and long-session thinking reduce operator fatigue
- strong instinct that solo-dev shipping includes docs, design, and continuity, not only coding

Forge should absorb:
- a clearer memory stack beyond basic `.brain/`
- better continuity restore for interrupted sessions
- a lightweight dashboard and stronger project intelligence extraction

Forge should avoid:
- scope sprawl into unrelated content and growth surfaces
- cloud-brain complexity before local-first value is strong
- turning Forge into a giant box of everything

## 4. get-shit-done

Identity:
- the most pragmatic spec-driven state machine in the set
- built for project state, planning phases, and shipping work on real repos

Strengths:
- best brownfield onboarding story through `map-codebase`
- explicit state artifacts for discussion, planning, execution, verify, ship, and health
- strong requirement-to-verification contract before implementation begins
- good bias toward repairability, not only creation

Forge should absorb:
- first-class `map-codebase`
- project-state artifacts for active work slices
- health and repair flows for plan drift and artifact drift

Forge should avoid:
- full command sprawl
- heavy visible artifact taxonomy when a lighter layer would do

## 5. antigravity-kit

Identity:
- a broad starter kit for agents, skills, workflows, and app templates

Strengths:
- immediate utility through simple install and broad stack coverage
- strong template mindset around app-builder and stack selection
- good source of reusable starter patterns for web, API, mobile, CLI, and extension work

Forge should absorb:
- first-party starter templates and golden-path presets
- app-builder style stack selection for a few chosen lanes
- reusable domain packs for deployment, testing, and stack setup

Forge should avoid:
- supporting too many stacks before depth exists anywhere
- shipping large template surfaces without verification and update contracts

## 6. oh-my-agent

Identity:
- a portable multi-agent harness with `.agents` as source of truth and generated host projections

Strengths:
- best source-of-truth architecture in the set for portable agents, skills, and workflows
- strong operator utilities such as doctor, dashboard, spawn, and parallel flows
- `stack-set` is highly reusable for generating stack-specific references
- serious preset thinking instead of asking users to build everything manually

Forge should absorb:
- a clearer canonical source model for portable skills and host projections
- `doctor` as a first-class environment and capability check
- preset-based installation and stack-aware generation

Forge should avoid:
- heavy MCP assumptions as a universal dependency
- orchestration complexity that exceeds solo-dev golden paths

## 7. OpenSpec

Identity:
- a spec-driven development framework built around change artifacts, not chat history

Strengths:
- strong artifact-guided workflow: propose, apply, archive
- every change gets a folder with `proposal.md`, `specs/`, `design.md`, and `tasks.md`
- philosophy is fluid, iterative, easy, and explicitly brownfield-friendly
- works across many AI tools and includes a dashboard concept
- archive step updates the long-lived spec surface after shipping

Forge should absorb:
- per-change artifact folders for medium and large work
- a clean archive loop that pushes shipped changes back into durable project knowledge
- brownfield-first spec layers that help the AI reason from explicit deltas, not only chats

Forge should avoid:
- forcing full spec ceremony on small edits
- turning solo-dev flow into markdown bureaucracy
- assuming spec artifacts alone replace strong verification

## 8. rune

Identity:
- a lean skill ecosystem built as a mesh, compiled across multiple AI IDEs

Strengths:
- compelling critique of isolated skill packs and rigid pipelines
- mesh model encourages resilient routing instead of linear failure-prone chains
- compiled intent mesh and intent-router hook reduce runtime guesswork
- privacy mesh is a serious pre-tool guard with allow, warn, and block behavior
- pack system and multi-platform compiler are stronger than most skill repos

Forge should absorb:
- compile-time routing hints and skill graph data in the registry
- a privacy and sensitive-operation guard before tool execution
- pack-style layering for lanes and optional extension bundles

Forge should avoid:
- pack sprawl into too many domains too early
- self-benchmark claims becoming the main product thesis
- turning Forge into a skill marketplace before it becomes a dependable ship tool

## 9. orchestrated-project-template

Identity:
- an opinionated Claude project scaffold with onboarding, specialist agents, living docs, and git conventions

Strengths:
- strong `/start` onboarding that fills placeholders before coding starts
- living documentation with clear ownership and update expectations
- `PRD.md` is treated as protected source of truth
- `TODO.md` is explicitly human territory, which is a healthy governance pattern
- git conventions, branch naming, and PR templates create useful delivery hygiene

Forge should absorb:
- stronger onboarding and setup protocol for new workspaces
- document ownership and docs-update-before-completion rules
- protected product intent artifacts and human-owned backlog patterns

Forge should avoid:
- a huge fixed roster of specialist personas
- Claude-specific assumptions leaking into the core product
- expanding into copy, SEO, and marketing roles before software shipping is excellent

## Cross-Repo Synthesis For Forge

What Forge already does well:
- host-neutral orchestration core
- verification discipline
- clean adapter boundary
- runtime-tool split with `forge-browse` and `forge-design`

What Forge is missing most:
- brownfield onboarding and `map-codebase`
- stronger continuity and project memory
- first-party lanes with starter templates
- spec or change artifacts that survive after chat history is gone
- operator ergonomics: doctor, dashboard, release-doc sync, release readiness

Highest-fit absorptions:
- from `superpowers`: evidence-before-claims, worktree discipline, staged review
- from `get-shit-done`: `map-codebase`, health, requirement-to-verification contract
- from `oh-my-agent`: doctor, presets, stack-set style generation
- from `OpenSpec`: per-change artifact workflow and archive-back-to-spec loop
- from `rune`: compiled routing hints and privacy guard
- from `antigravity-kit`: starter templates for selected lanes
- from `codymaster`: continuity, decisions, learnings, dashboard instinct
- from `gstack`: shipping loop completeness, browser QA, docs sync, deploy confidence
- from `orchestrated-project-template`: onboarding, living docs, protected intent artifacts, human-owned backlog

Recommended Forge direction at audit time:
- `Forge Core`: orchestration, verification, adapters, runtime tools
- `Forge Lanes`: first-party solo-dev lanes, starting with a web-product lane and leaving lane 2 intentionally open until later evidence arrives
- `Forge Ops`: `doctor`, `map-codebase`, `verify`, `ship`, `release-doc`, `dashboard`, `canary`
- `Forge Memory`: continuity, decisions, learnings, searchable project intelligence
- `Forge Artifacts`: durable change folders for medium and large work

Concrete next steps:
1. Build `forge doctor`.
2. Build `forge map-codebase`.
3. Add continuity plus decisions and learnings schema upgrades.
4. Extend `init` into lane-aware presets, not just skeleton folders.
5. Commit to one first-party lane first: Next.js + TypeScript + Postgres. Treat FastAPI + Postgres as an early candidate, not a committed second lane.
6. Add change-artifact and archive flows for medium and large work.
7. Strengthen `forge-browse` for persistent authenticated QA sessions.
8. Add release-doc drift correction after ship.

## Bottom Line

The nine repos point in the same direction:
- solo devs do not need more generic prompting
- they need a system that remembers, scaffolds, verifies, reviews, tests, and ships

Forge already has the kernel to become that system.
What it needs next is not more extensibility.
It needs stronger first-party lanes, sharper operator ergonomics, and durable product artifacts centered on real shipping.
