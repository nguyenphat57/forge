# Forge Help/Next

> Goal: keep `help` and `next` in `forge-core` repo-first, host-neutral, and reusable for future adapters.

## Core Contract

- Engine canonical: `scripts/resolve_help_next.py`
- Workflow wrappers: `workflows/operator/help.md` and `workflows/operator/next.md`
- Preferred sources:
  1. `git status`
  2. `docs/plans/` and `docs/specs/`
  3. `.brain/session.json`
  4. `.brain/handover.md`
  5. `README`

## Stage Model

|Stage | When|
|------|---------|
|`blocked` | session or handover shows the blocker clearly|
|`session-active` | Have clear ongoing tasks or pending tasks|
|`active-changes` | working tree has new diff / files|
|`planned` | No code yet but has the latest plan/spec|
|`unscoped` | The repo does not yet show an active slice|

## Output Contract

- `current_focus`
- `suggested_workflow`
- `recommended_action`
- `alternatives` maximum 2 items
- `evidence`
- `warnings`

## Guardrails

- Do not mistake `help/next` for a lengthy recap.
- Do not suggest ritual session legacy.
- Do not give a vague next step if the slice can be more specifically defined.
- When the context is weak, it must be clearly stated that the repo does not have enough signals.

## Adapter Boundary

- Host adapters may expose `/help` and `/next` as thin wrappers.
- The active host adapter should keep natural-language first and can leave slash as an optional alias.
- The adapter cannot fork stage model or source priority.
