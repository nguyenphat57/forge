# Forge Codex Smoke Tests

Goal: confirm the Codex host activates Forge sibling skills through `forge-codex` and no legacy global orchestration remains active.

## How to use

- Run each prompt in a fresh or clean thread when possible.
- Do not tell the agent the expected skill in advance.
- Record results in `smoke-test-checklist.md`.
- Prefer natural-language prompts first, then verify optional slash aliases.

## Pass criteria

- Global host resolves to `forge-codex`.
- Natural-language prompts remain the primary surface.
- Repo-first and evidence-first behavior stay intact.
- No legacy recap or save ritual is suggested.
- No legacy AWF runtime artifacts are required for any skill activation.

## Prompt Pack

### CT-01: Natural-language restore

```text
Continue the task we were working on yesterday and tell me the best next step.
```

Expected:

- Invokes `forge-session-management`
- Restores from repo/docs/plan first
- Ends with one actionable next step

### CT-02: Help alias

```text
/help
```

Expected:

- Uses the `help` audit sidecar
- Uses repo state rather than recap theater

### CT-03: Next step from repo

```text
What should I do next from the current repo state?
```

Expected:

- Uses the `next` audit sidecar
- Returns one concrete next action

### CT-04: Run a command

```text
Run `npm test` and tell me whether the next move is test, debug, or deploy.
```

Expected:

- Uses the `run` operator wrapper
- Executes the real command
- Classifies the next skill or wrapper from evidence

### CT-05: Build alias

```text
/code
Add CSV export for orders.
```

Expected:

- Invokes `forge-executing-plans`
- Requires one failing test first when a viable harness exists

### CT-06: Debug alias

```text
/debug
Fix the checkout crash that happens after release.
```

Expected:

- Invokes `forge-systematic-debugging`
- Investigates root cause before suggesting a fix

### CT-07: Review alias

```text
/review
Review the current changes before merging.
```

Expected:

- Invokes `forge-requesting-code-review`
- Findings come first

### CT-08: Customize

```text
/customize
Give shorter answers, move faster, and keep feedback directly.
```

Expected:

- Uses the `customize` operator wrapper
- Keeps canonical preference keys

### CT-09: Init

```text
/init
Bootstrap this workspace for Forge, then tell me whether brainstorm or plan should come next.
```

Expected:

- Uses the `init` operator wrapper
- Keeps workspace bootstrap thin
- Does not overwrite existing repo files

### CT-10: Delegate independent slices

```text
/delegate
Split the independent checkout UI and API slices across subagents, keep write scopes isolated, and review each slice independently.
```

Expected:

- Invokes `forge-dispatching-parallel-agents`
- Requires explicit ownership before delegation
- Keeps reviewer lanes independent
- Refuses parallel dispatch if boundaries are not actually clear
