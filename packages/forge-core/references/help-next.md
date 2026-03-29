# Forge Help/Next

> Goal: keep `help` and `next` repo-first, host-neutral, and reusable across adapters.

## Core Contract

- Canonical engine: `scripts/resolve_help_next.py`
- Workflow wrappers: `workflows/operator/help.md` and `workflows/operator/next.md`
- Preferred sources, in order:
  1. `git status`
  2. `docs/plans/` and `docs/specs/`
  3. active change artifact or `.forge-artifacts/workflow-state/<project>/latest.json`
  4. `.brain/session.json`
  5. `.brain/handover.md`
  6. `README`

## Stage Model

| Stage | When |
|---|---|
| `blocked` | Session or handover clearly shows a blocker |
| `session-active` | There is an active task or a pending task list |
| `active-changes` | The working tree contains active diffs or new files |
| `change-active` | A durable change artifact or workflow-state record is present |
| `planned` | No code exists yet, but there is a current plan or spec |
| `unscoped` | The repo does not show an active work slice |

## Output Contract

- `current_focus`
- `suggested_workflow`
- `recommended_action`
- `alternatives` with at most 2 items
- `evidence`
- `warnings`

## Guardrails

- Do not turn `help` or `next` into a long recap.
- Do not suggest legacy recap or save rituals.
- Do not give a vague next step when the slice can be named more precisely.
- For medium+ work, prefer answers that point at the durable artifact to create or refresh next.
- When context is weak, say clearly that the repo does not provide enough signal.

## Adapter Boundary

- Host adapters may expose `/help` and `/next` as thin wrappers.
- The active host adapter should stay natural-language first and keep slash commands optional.
- The adapter must not fork the stage model or source priority.
