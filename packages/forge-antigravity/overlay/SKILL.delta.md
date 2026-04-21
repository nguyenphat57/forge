---
name: forge-antigravity
description: "Forge Antigravity - skill-oriented orchestrator optimized for Antigravity workspaces. Use when a request needs Forge routing, verification guardrails, Antigravity-native wrappers, and natural-language session handling."
---

# Forge Antigravity - Core Orchestrator

> Forge Antigravity maps the Forge evidence-first kernel onto Gemini workspaces through `GEMINI.md`, Antigravity-native operator wrappers, and the same shared verification contract as core.

## Host Boundary

- Antigravity host rules live above this folder.
- `GEMINI.global.md` is the canonical global host entry template for installed runtime.
- `AGENTS.md` at the workspace root is a router or instruction file, not `SKILL.md`.
- This adapter owns the Antigravity-facing surface while routing and verification remain core.

## Antigravity Protocol Bridge

- Forge concepts map onto Antigravity host tools instead of duplicating ceremony.
- Activation, chain progress, and verification reporting should stay aligned with the host protocol while preserving Forge stage semantics.
- Host UX can be richer, but it must not fork the meaning of Forge skills, packets, or evidence reporting.

## Antigravity Artifact Boundary

- `.forge-artifacts/` remains the durable workspace-scoped home for Forge tooling output.
- Conversation-scoped Antigravity artifacts stay in the host-managed `brain/` area.
- Do not mix Forge deterministic artifacts with host conversation artifacts.

## Response Personalization

- At the start of each new thread, resolve preferences before the first substantive user-facing reply.
- Read adapter-global state from `state/preferences.json`, using `scripts/resolve_preferences.py` when a merged payload is needed.
- `forge-antigravity` may expose `/customize`, but durable updates still go through `scripts/write_preferences.py`.
- Clean installs default to Vietnamese with full diacritics until state or workspace overrides them.

## Antigravity Operator Surface

- Primary wrappers are `/help`, `/next`, `/run`, `/bump`, `/rollback`, `/customize`, and `/init`.
- Natural-language session requests stay primary: `resume`, `continue`, `save context`, and `handover`.
- `quality-gate` and `deploy` keep their shared core meaning inside Antigravity bundles.
- Wrapper UX may be richer, but deterministic semantics still come from core scripts and workflows.

## Activation Announcement

```text
Forge Antigravity: orchestrator | route intent correctly, evidence before claims
```
