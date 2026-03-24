# Forge Codex Smoke Tests

Goal: confirm the Codex host routes into `forge-codex` and no legacy global orchestration remains active.

## How to use

- Run each prompt in a fresh or clean thread when possible.
- Do not tell the agent the expected route in advance.
- Record results in `smoke-test-checklist.md`.
- Prefer natural-language prompts first, then verify optional slash aliases.

## Pass criteria

- Global host routing resolves to `forge-codex`.
- Natural-language prompts remain the primary surface.
- Repo-first and evidence-first behavior stay intact.
- No legacy recap or save ritual is suggested.
- No legacy AWF runtime artifacts are required for any route.

## Prompt Pack

### CT-01: Natural-language restore

```text
Continue the task we were working on yesterday and tell me the best next step.
```

Expected:

- Routes to `workflows/execution/session.md`
- Restores from repo/docs/plan first
- Ends with one actionable next step

### CT-02: Help alias

```text
/help
```

Expected:

- Routes to `workflows/operator/help.md`
- Uses repo state rather than recap theater

### CT-03: Next step from repo

```text
What should I do next from the current repo state?
```

Expected:

- Routes to `workflows/operator/next.md`
- Returns one concrete next action

### CT-04: Run a command

```text
Run `npm test` and tell me whether the next move is test, debug, or deploy.
```

Expected:

- Routes to `workflows/operator/run.md`
- Executes the real command
- Classifies the next workflow from evidence

### CT-05: Build alias

```text
/code
Add CSV export for orders.
```

Expected:

- Routes to `workflows/execution/build.md`
- States verification before editing behavior

### CT-06: Debug alias

```text
/debug
Fix the checkout crash that happens after release.
```

Expected:

- Routes to `workflows/execution/debug.md`
- Investigates root cause before proposing a fix

### CT-07: Review alias

```text
/review
Review the current change before merge.
```

Expected:

- Routes to `workflows/execution/review.md`
- Findings come first

### CT-08: Customize

```text
/customize
Give shorter answers, move faster, and keep feedback direct.
```

Expected:

- Routes to `workflows/operator/customize.md`
- Keeps canonical preference keys

### CT-09: Init

```text
/init
Bootstrap this workspace for Forge, then tell me whether brainstorm or plan should come next.
```

Expected:

- Routes to `workflows/operator/init.md`
- Keeps workspace bootstrap thin
- Does not overwrite existing repo files
