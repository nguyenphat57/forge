# Forge Help/Next

> Goal: keep `help` and `next` repo-first, host-neutral, and reusable across adapters.

## Core Contract

- Canonical engine: `scripts/resolve_help_next.py`
- Workflow wrappers: `workflows/operator/help.md` and `workflows/operator/next.md`
- Strategic policy filter for Forge-maintenance choices: `references/target-state.md`
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
| `mapped` | A codebase map is present and the repo has enough brownfield context to choose the first slice |
| `unscoped` | The repo does not show an active work slice |

## Stage-To-Entrypoint Hints

| Stage | First operator move |
|---|---|
| `blocked` | `doctor` if workspace/runtime health is uncertain, otherwise inspect the blocker and reopen the right workflow |
| `mapped` | use `plan`, `spec-review`, or a direct task prompt now that the brownfield map exists |
| `unscoped` | `map-codebase` first for existing repos, `brainstorm` first for greenfield repos |
| `change-active` | `dashboard` or `next` to resume the recorded slice instead of rediscovering context |

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
- If a repo is already mapped, prefer reusing that brownfield summary before re-scanning the repo.
- When context is weak, say clearly that the repo does not provide enough signal.
- When operating on Forge itself or choosing between multiple valid Forge directions, prefer the move that best matches `references/target-state.md`.

## Adapter Boundary

- Host adapters may expose `/help` and `/next` as thin wrappers.
- The active host adapter should stay natural-language first and keep slash commands optional.
- The adapter must not fork the stage model or source priority.
