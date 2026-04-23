# Forge Help/Next

> Goal: keep the internal guidance engine repo-first, host-neutral, and reusable by session continuity and smoke tooling.

## Core Contract

- Canonical internal engine: `commands/resolve_help_next.py`
- Public operator wrappers for `help` and `next` are retired.
- Strategic policy filter for Forge contract-sensitive choices: `docs/current/target-state.md`
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

## Stage-To-Workflow Hints

| Stage | First workflow move |
|---|---|
| `blocked` | inspect the blocker, reopen the right workflow, and only use recorded runtime recovery guidance when browser proof tooling is stale |
| `planned` | use `plan`, or reopen `brainstorm` with the architectural lens if the design boundary is still unclear |
| `unscoped` | run `python scripts/verify_repo.py --profile fast` if repo health is unclear, then state one bounded slice |
| `change-active` | use the recorded workflow-state slice instead of rediscovering context |

## Output Contract

- `current_stage`
- `current_focus`
- `suggested_workflow`
- `recommended_action`
- `alternatives` with at most 2 items
- `evidence`
- `warnings`

## Guardrails

- Do not turn guidance or next-step selection into a long recap.
- Do not suggest legacy recap or save rituals.
- Do not give a vague next step when the slice can be named more precisely.
- For medium+ work, prefer answers that point at the durable artifact to create or refresh next.
- When context is weak, say clearly that the repo does not provide enough signal.
- If runtime health is stale or broken for browser proof, recommend the recorded runtime recovery command or guidance before retrying packet proof claims.
- When operating on Forge itself or choosing between multiple valid Forge directions, prefer the move that best matches `docs/current/target-state.md`.

## Adapter Boundary

- Host adapters should keep guidance and next-step requests natural-language first.
- The adapter must not fork the stage model or source priority.

