---
name: forge-codex
description: "Forge Codex - Codex-oriented adapter for Forge core. Use when a request needs Forge routing, verification guardrails, Codex-native operator wrappers, and optional native delegation."
---

# Forge Codex - Host Adapter

> Forge Codex maps the Forge execution kernel and orchestration system onto Codex through `AGENTS.md`, natural-language first operator wrappers, and native delegation when the slice is safe to split.

## Host Boundary

- `AGENTS.md` is Codex's primary routing and instruction file, but it does not replace `SKILL.md`.
- `AGENTS.global.md` is the canonical global host entry template when Codex should point only to Forge.
- This adapter owns the Codex-facing surface; routing policy, verification rules, and registry data still come from Forge core.
- If the workspace has no local layer, Forge Codex must still run well with this bundle alone.

## Response Personalization

- At the start of each new thread, resolve preferences before the first substantive user-facing reply.
- Read adapter-global state from `state/preferences.json`, using `scripts/resolve_preferences.py` when a merged payload is needed.
- `forge-codex` responds in Vietnamese with full diacritics when resolved `language=vi`; broken Vietnamese encoding is a defect.
- `workflows/operator/customize.md` stays thin and must continue to write through `scripts/write_preferences.py`.

## Codex Operator Surface

- `forge-codex` is natural-language first; slash commands are optional aliases.
- Primary entry points are `help`, `next`, `run`, `delegate`, `bump`, `rollback`, `customize`, and `init`.
- `dispatch-subagents` is the native Forge/Codex bridge for safe multi-agent work.
- `workflows/operator/customize.md` and `workflows/operator/init.md` are thin wrappers over core scripts.
- `quality-gate` and `deploy` keep the shared core contract inside Codex bundles.

## Codex Multi-Agent Delegation

- When routing selects a parallel-safe lane, load `workflows/execution/dispatch-subagents.md`.
- Keep clear ownership, independent packets, and explicit review lanes instead of duplicating the whole thread context by default.
- Codex-native delegation refines execution strategy; it does not replace Forge packets, verification, or workflow-state contracts.

## Activation Announcement

```text
Forge Codex: execution kernel + orchestration | route the right intent, keep evidence before claims
```
