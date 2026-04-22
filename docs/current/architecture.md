# Forge Current Architecture

## Goal

Describe the live Forge architecture after the split-skill cutover, without sending maintainers through archived roadmap material to understand current behavior.

## Current Topology

- `packages/forge-core/` owns the host-neutral contract: bootstrap wording, workflow-state semantics, verification invariants, operator/session compatibility wrappers, and preference/state tooling.
- `packages/forge-skills/` is the source of truth for host-discoverable Forge process skills such as `forge-brainstorming`, `forge-writing-plans`, `forge-systematic-debugging`, and `forge-verification-before-completion`.
- `packages/forge-core/workflows/` is operator/session compatibility only. These files keep continuity wrappers working, but they point back to sibling skills.
- `packages/forge-codex/overlay/` and `packages/forge-antigravity/overlay/` adapt the shared contract to host-native bootstrap files, installed skill layout, and operator wrappers.
- `docs/current/` is the live maintainer-facing explanation surface; `docs/archive/` is historical context only.

## Control Architecture

- Forge is markdown-first. Control lives in small host-discoverable skills, design docs, implementation plans, checklists, and workflow-state artifacts.
- Forge is workflow-first in behavior, but workflow selection now happens through bootstrap markdown and sibling skill activation rather than a deterministic routing engine.
- The 1% rule applies before any substantive response or action: if a relevant Forge skill might apply, load it first.
- Process skills run before implementation skills: brainstorm, debug, and session management gate behavioral build, bugfix, and resume work.
- `help` and `next` are audit/resume sidecars over durable artifacts. They explain current state and the next bounded action, but they do not choose process by heuristic routing.
- Deterministic scripts remain part of the architecture for invariants, state, preferences, install, and verification. They are not the public workflow control plane.

## Public Versus Internal Surfaces

Public contract:

- natural language first
- host-native Forge sibling skills as the activation surface
- operator/session wrapper paths that invoke skills, not workflow internals
- artifact-backed `help` and `next`
- explicit evidence before claims

Internal support surface:

- workflow-state projection and refresh
- preference resolution and writes
- invariant verification and bundle checks
- operator/session wrappers for continuity requests
- route-era helpers kept only for archived tests, deterministic inspection, or compatibility support

`route_preview is not the current public contract`. If route-era files still exist, they are internal or historical support, not the operating model.

## Python Boundary

Python remains appropriate for:

- invariant checks
- workflow-state persistence and projections
- preference resolution and durable writes
- release/build/install verification

Python should not be the first thing maintainers teach or users learn for routine skill selection, navigation, or control semantics that are now expressed in markdown.

## Maintainer Reading Path

- Start here for the live architecture.
- Read [operator-surface.md](/C:/Users/Admin/.gemini/forge/.forge-artifacts/worktrees/markdown-first-control/docs/current/operator-surface.md) for the thin operator contract and `help`/`next` sidecar semantics.
- Read [install-and-activation.md](/C:/Users/Admin/.gemini/forge/.forge-artifacts/worktrees/markdown-first-control/docs/current/install-and-activation.md) for source-repo versus installed-runtime activation and sibling skill installation.
- Read [target-state.md](/C:/Users/Admin/.gemini/forge/docs/current/target-state.md) when a change could alter Forge identity, process weight, or invariant boundaries.

## Current repo posture

- The current repo posture is a skill-split contract cutover, not product expansion.
- Changes should default to drift correction, compatibility repair, docs and bootstrap alignment, and verification hardening.
- New helper scripts or host affordances are acceptable only when they reinforce the sibling-skill contract instead of competing with it.
