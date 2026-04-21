---
name: forge-antigravity
description: "Forge Antigravity - skill-oriented orchestrator optimized for Antigravity workspaces. Use when a request needs Forge routing, verification guardrails, Antigravity-native wrappers, and natural-language session handling."
---

# Forge Antigravity - Core Orchestrator

> Forge Antigravity maps the Forge process-first kernel onto Gemini workspaces through `GEMINI.md`, Antigravity-native operator wrappers, and the same shared verification contract as core.

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
- Forge no longer inserts a separate pre-build review stage for boundary-sensitive `BUILD` work; behavioral build routing stays flat and relies on the shared plan/build/review contract instead.
- Forge keeps packet semantics stable across `parallel-split`, `independent-reviewer`, and `controller-sequential`; host capability changes lane execution, not the packet contract.
- Use `scripts/route_preview.py` when routing must be previewed deterministically.
- Canonical thresholds, chains, and lane policy live in `data/orchestrator-registry.json`.

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
Forge Antigravity: orchestrator | route intent correctly, evidence before claims
```
