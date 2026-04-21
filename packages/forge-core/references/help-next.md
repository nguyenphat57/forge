# Forge Help/Next

> Goal: keep `help` and `next` repo-first, host-neutral, and reusable across adapters.

## Core Contract

- Canonical engine: `scripts/resolve_help_next.py`
- Workflow wrappers: `workflows/operator/help.md` and `workflows/operator/next.md`
- Strategic policy filter for Forge-maintenance choices: `references/target-state.md`
- Preferred sources, in order:
  1. `git status`
  2. `.forge-artifacts/workflow-state/<project>/latest.json` when execution or stage state is already persisted
  3. `.forge-artifacts/workflow-state/<project>/packet-index.json` for low-cost continuity resume
  4. `docs/plans/` and `docs/specs/` as sidecars when workflow-state is missing, incomplete, or not seeded yet
  5. `.brain/session.json`
  6. `.brain/handover.md`
  7. `README`

## Stage Model

| Stage | When |
|---|---|
| `blocked` | Session or handover clearly shows a blocker |
| `session-active` | There is an active task or a pending task list |
| `active-changes` | The working tree contains active diffs or new files |
| `change-active` | A workflow-state record or recorded stage is present |
| `planned` | No code exists yet, but there is a current plan or spec |
| `unscoped` | The repo does not show an active work slice |

## Stage-To-Entrypoint Hints

| Stage | First operator move |
|---|---|
| `blocked` | inspect the blocker, reopen the right workflow, and only use recorded runtime recovery guidance when browser proof tooling is stale |
| `planned` | use `plan`, `architect`, or a direct task prompt now that a bounded slice exists |
| `unscoped` | run `python scripts/verify_repo.py --profile fast` if repo health is unclear, then state one bounded slice |
| `change-active` | use `next` to resume the recorded slice instead of rediscovering context |

## Output Contract

- `current_stage`
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
- If runtime health is stale or broken for browser proof, recommend the recorded runtime recovery command or guidance before retrying packet proof claims.
- When operating on Forge itself or choosing between multiple valid Forge directions, prefer the move that best matches `references/target-state.md`.

## Adapter Boundary

- Host adapters may expose `/help` and `/next` as thin wrappers.
- The active host adapter should stay natural-language first and keep slash commands optional.
- The adapter must not fork the stage model or source priority.
