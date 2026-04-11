# Forge Adapter Boundary

## Goal

Keep `forge-core` clean enough to support current adapters and future adapters such as `forge-claude` without refactoring the core story every time a new host appears.

## Overlay Delta Versus Materialized Bundle

- `packages/<adapter>/overlay/` is the editable adapter delta, not a full bundle.
- `dist/<adapter>/` is the materialized bundle after core, generated artifacts, and the overlay delta are combined.
- When a capability appears in `dist/<adapter>/` but not in `packages/<adapter>/overlay/`, it is inherited from `forge-core` rather than duplicated in adapter source.
- Materialized adapter registries live in `dist/<adapter>/data/orchestrator-registry.json` and are the contract tests should read.
- Overlay edits should stay small and explicit so the materialized bundle remains reproducible from source.

## Hard Rule

If a capability cannot be used almost unchanged by:

- `forge-antigravity`
- `forge-codex`
- a future adapter such as `forge-claude`

then it does not belong in `forge-core` by default.

## `forge-core` may contain

- host-neutral routing, verification, and orchestration logic
- shared workflows that make sense across hosts
- shared references, schemas, and deterministic tooling
- response-style engines and preferences schemas, if the behavior is host-neutral
- adapter-agnostic naming and examples

## `forge-core` must not contain

- references to a specific host command surface such as `/run` or `/help` as a required interface
- host instruction files such as `GEMINI.md`, `AGENTS.md`, or future host-specific memory files as core dependencies
- UI metadata, host chips, or marketplace/install metadata
- compatibility aliases that only exist to mimic one host or framework
- onboarding flows tailored to one host's user base
- examples or fixtures that assume one adapter name when a neutral placeholder works

## Adapter responsibilities

Adapters own:

- host entry files
- host command aliases and wrapper UX
- host-specific onboarding and session phrasing
- host metadata and installation surfaces
- thin mapping from host surface to Forge core capabilities
- adapter docs that describe how overlay deltas become materialized release bundles
- host-specific wording for the same core release gate contract, not new release posture semantics

Examples of adapter-only wrappers:

- `customize` and `init` when they are host-facing UX around shared core scripts such as `write_preferences.py` and `initialize_workspace.py`
- Antigravity-only session phrasing and natural-language guidance
- Codex-native delegation surfaces such as `dispatch-subagents.md`

## Decision test for new features

Before adding anything to `forge-core`, answer:

1. Would this still make sense for a future `forge-claude` adapter?
2. Does it depend on one host's instruction file, slash command grammar, or UI surface?
3. Is this a core capability, or only a wrapper around a core capability?
4. Can the same outcome be achieved by keeping the engine in core and the UX wrapper in an adapter?

If questions `1` and `4` are weak, or `2` is yes, the change should stay out of `forge-core`.

## Review checklist

- `forge-core` wording stays host-neutral
- examples and fixtures use neutral placeholders where possible
- host-specific aliases live in adapters
- no new dependency on one host's instruction surface is introduced
- the change would still be valid for a future `forge-claude` adapter
- the materialized `dist/<adapter>/` bundle still reads as a thin, reproducible composition of core plus overlay
- release wording matches the core `quality-gate` and `deploy` contract instead of inventing adapter-local posture names
