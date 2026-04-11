---
name: forge-codex
description: "Forge Codex - Codex-oriented adapter for Forge core. Use when a request needs Forge routing, verification guardrails, Codex-native operator wrappers, and optional native delegation."
---

# Forge Codex - Host Adapter

> Forge Codex maps the Forge process-first kernel onto Codex through `AGENTS.md`, natural-language first operator wrappers, and native delegation when the slice is safe to split.

## Host Boundary

- `AGENTS.md` is Codex's primary routing and instruction file, but it does not replace `SKILL.md`.
- `AGENTS.global.md` is the canonical global host entry template when Codex should point only to Forge.
- This adapter owns the Codex-facing surface; routing policy, verification rules, and registry data still come from Forge core.
- If the workspace has no local layer, Forge Codex must still run well with this bundle alone.

## Bootstrap Rules

- Forge is the global-first orchestrator for real repos.
- Natural language is the primary surface; host aliases are optional wrappers.
- Read only the files needed for the current task.
- Workspace-local routers and companion skills are optional augmentation, not replacements.
- Keep scope minimal. Ask before schema changes, folder-structure changes, or new dependencies.
- Canonical machine-readable routing policy lives in `data/orchestrator-registry.json`.
- Current deterministic tooling entrypoint lives in `references/kernel-tooling.md`.

## Routing Contract

- Detect intent and complexity first, then choose the smallest Forge chain that can finish the work safely.
- `REVIEW`, `SESSION`, and truly small tasks may stay prompt-led.
- Medium or large `BUILD` or `VISUALIZE` work that is still ambiguous must go through `brainstorm` before `plan`.
- High-risk `BUILD` work must go through `spec-review` before `build`.
- Forge keeps packet semantics stable across `parallel-split`, `independent-reviewer`, and `controller-sequential`; host capability changes lane execution, not the packet contract.
- Use `scripts/route_preview.py` when routing must be previewed deterministically.
- Canonical thresholds, chains, and lane policy live in `data/orchestrator-registry.json`.

## Response Personalization

- At the start of each new thread, resolve preferences before the first substantive user-facing reply.
- Read adapter-global state from `state/preferences.json` and `state/extra_preferences.json`, using `scripts/resolve_preferences.py` when a merged payload is needed.
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

## Verification Contract

- proof before claims is non-negotiable.
- Define verification before editing when behavior changes.
- With a viable harness, start from a failing test or reproduction.
- Without a harness, use the strongest available smoke, build, lint, typecheck, diff, or manual reproduction and say why.
- `quality-gate` is the canonical go / no-go surface for merge-ready and deploy claims.
- `deploy` only happens after fresh verification and explicit release posture.
- If verification cannot run, say `not verified`, name the blocker, and keep residual risk explicit.

## Solo Profile And Workflow-State Contract

- `solo-internal` and `solo-public` are overlays for one operator, not separate orchestration systems.
- For solo-profile release-sensitive work, keep the tail explicit as `self-review` -> `secure` -> `quality-gate` -> `deploy`.
- Release-facing posture, rollout confidence, and follow-up risk notes live in `quality-gate`, `deploy`, and workflow-state instead of separate release-tail workflows.
- workflow-state records use the canonical stage status vocabulary: `pending`, `required`, `active`, `completed`, `skipped`, `blocked`.
- workflow-state entries carry activation reasons and skip reasons so the gate does not have to reconstruct intent from chat memory.
- There is no `/gate` alias; `quality-gate` stays the stage name.

## Skill Laws

- `brainstorm`: no ambiguous medium or large work without choosing a direction first.
- `plan`: no medium or large build without a confirmed plan.
- `spec-review`: no high-risk build without a build-readiness review first.
- `build`: no behavioral change without defining verification first.
- `review`: findings first, summary second.
- `refactor`: no refactor without baseline and after verification.
- `run`: execute the real command, then route from evidence.
- VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION.

## Reference Map

- Quick entry point for current docs and references: `references/reference-map.md`.
- Use `references/kernel-tooling.md` when you need deterministic scripts instead of prose.

## Activation Announcement

```text
Forge Codex: orchestrator | route the right intent, keep evidence before claims
```
