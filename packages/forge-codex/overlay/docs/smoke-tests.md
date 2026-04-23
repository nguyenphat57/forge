# Forge Codex Smoke Tests

Goal: confirm the Codex host activates Forge sibling skills through `forge-codex` and no legacy global orchestration remains active.

## How to use

- Run each prompt in a fresh or clean thread when possible.
- Do not tell the agent the expected skill in advance.
- Record results in `smoke-test-checklist.md`.
- Prefer natural-language prompts first, then verify explicit skill invocation or plain action names when needed.

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

### CT-02: Help from repo state

```text
Help me figure out the next step from the repo state.
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

### CT-05: Execute a build-oriented request

```text
Add CSV export for orders.
```

Expected:

- Invokes `forge-executing-plans`
- Requires one failing test first when a viable harness exists

### CT-06: Debug request

```text
Fix the checkout crash that happens after release.
```

Expected:

- Invokes `forge-systematic-debugging`
- Investigates root cause before suggesting a fix

### CT-07: Review request

```text
Review the current changes before merging.
```

Expected:

- Invokes `forge-requesting-code-review`
- Findings come first

### CT-08: Durable preference change

```text
Give shorter answers, move faster, and keep feedback directly.
```

Expected:

- Invokes `forge-customize` or the equivalent natural-language preference flow
- Keeps canonical preference keys

### CT-09: Bootstrap

```text
Bootstrap this workspace for Forge with canonical docs, then tell me whether brainstorm or plan should come next.
```

Expected:

- Invokes `forge-init`
- Keeps workspace bootstrap thin
- Does not overwrite existing repo files

### CT-10: Delegate independent slices

```text
Split the independent checkout UI and API slices across subagents, keep write scopes isolated, and review each slice independently.
```

Expected:

- Invokes `forge-dispatching-parallel-agents`
- Requires explicit ownership before delegation
- Keeps reviewer lanes independent
- Refuses parallel dispatch if boundaries are not actually clear
