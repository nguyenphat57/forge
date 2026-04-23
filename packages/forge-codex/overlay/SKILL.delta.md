---
name: forge-codex
description: "Forge Codex - Codex adapter for Forge core. Use when a request needs Forge sibling skills, verification guardrails, Codex-native operator wrappers, and optional native delegation."
---

# Forge Codex - Host Adapter Delta

> Forge Codex maps the Forge evidence-first kernel onto Codex through `AGENTS.md`, host-native sibling skills, natural-language operator wrappers, and native delegation when the slice is safe to split.

## Host Boundary

- `AGENTS.md` is Codex's global bootstrap surface, but it does not replace sibling Forge skills.
- `AGENTS.global.md` is the canonical global host entry template when Codex should point only to Forge.
- This adapter owns Codex-facing wording and access mapping only.
- Core bootstrap and sibling skill markdown define process meaning.
- If the workspace has no local layer, Forge Codex must still run well with this bundle plus installed sibling skills.

## Response Personalization

- At the start of each new thread, resolve preferences before the first substantive user-facing reply.
- Read adapter-global state from `state/preferences.json`, using `scripts/resolve_preferences.py` when a merged payload is needed.
- `forge-codex` responds in Vietnamese with full diacritics when resolved `language=vi`; broken Vietnamese encoding is a defect.
- `workflows/operator/customize.md` stays thin and must continue to write through `scripts/write_preferences.py`.

## Codex Operator Surface

- `forge-codex` is natural-language first.
- Primary operator entrypoints are `help`, `next`, `run`, `bump`, `customize`, and `init`.
- `delegate` maps to `forge-dispatching-parallel-agents` when a concise operator action name helps.
- `workflows/operator/customize.md` and `workflows/operator/init.md` are thin wrappers over core scripts.
- Completion claims use `forge-verification-before-completion`; branch closure uses `forge-finishing-a-development-branch`.

## Codex Multi-Agent Delegation

- When parallel slices are safe, invoke `forge-dispatching-parallel-agents`.
- When a written plan should be split into worker or reviewer lanes, invoke `forge-subagent-driven-development`.
- Keep clear ownership, independent packets, and explicit review lanes instead of duplicating the whole thread context by default.
- Codex-native delegation refines execution strategy; it does not replace Forge packets, verification, or workflow-state contracts.

## Activation Announcement

```text
Forge Codex: orchestrator | invoke the right skill, keep evidence before claims
```
