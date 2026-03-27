---
name: session
type: flexible
triggers:
  - resume/continue/context restore
  - explicit save/handover request
  - shortcut: /save-brain, /recap
quality_gates:
  - Context restored or handover note restored
  - Response personalization resolved from adapter-global split preferences state when available
  - Scope-filtered continuity used when available
  - Structured continuous capture stays evidence-backed and scoped
---

# Session - Context & Session Management

> Goal: recover context from real artifact, don't rely on synthetic memory if not needed. This version assumes `.brain` is the workspace's default memory layer when the host supports this local memory layer.

<HARD-GATE>
- Do not fabricate token usage, context %, or "memory is almost full".
- Do not use `.brain` instead of repo state when the actual source-of-truth is available.
- Do not load all memory if the current scope only needs a smaller slice.
- Do not capture `decision` or `learning` if it does not have evidence, is not durable enough, or does not have a clear scope attached.
</HARD-GATE>

## Modes

|Triggers | Mode | Action|
|---------|------|-----------|
|`/recap`, `/recap full`, `/recap deep`, "continue", "resume" | **Restore** | Rebuild context from repo/doc/plan/.brain|
|`/save-brain`, "save progress" | **Save** | Write a short note or update `.brain` if the user wants|
|Explicit handover request | **Handover** | Create concise transfer notes|

---

## Operating Rules

- Global preferences live in adapter-global split state: canonical fields in `state/preferences.json`, adapter extras in `state/extra_preferences.json`, and only fall back to `.brain/preferences.json` for legacy workspaces that still need migration.

- Repo-first: priority `git status`, changed files, docs, plans, task notes.
- `.brain` is opt-in: only read/write when the user requests or handover really reduces risk.
- Do not make `/save-brain` a mandatory end-of-task ritual.
- If you have memory, read according to the smallest scope enough to use: global -> module -> current task, do not load it everywhere.

---

## Restore Mode (`/recap`)

In the host there is an equivalent shortcut:
- `/recap` -> quick restore
- `/recap full` -> restore more extensively if the host supports it
- `/recap deep` -> restore more deeply if the host supports it

### Load Order
```
1. docs/plans/, docs/specs/, open task notes
2. git status / changed files / recent commits (if git exists)
3. Adapter-global split preferences state (`state/preferences.json` + `state/extra_preferences.json`) via `python scripts/resolve_preferences.py --workspace <workspace> --format json`
4. .brain/handover.md
5. .brain/session.json
6. .brain/decisions.json
7. .brain/learnings.json
8. .brain/brain.json
```

### Response Personalization

Resolve adapter-global Forge preferences before recapping:

```powershell
python scripts/resolve_preferences.py --workspace <workspace> --format json
```

Payload resolved:
- terminology / tone
- recap and detail levels
- program proposed next step
- pace / feedback / personality of phrasing

It is not possible to dump raw schema for users unless otherwise requested; The main source of data is style, there is no way to restore it with preferences.

### Scope-Filtered Continuity

When `.brain` has enough data, drag only the relevant part:

```text
1. Determine the current scope: feature, module, subsystem, or file cluster
2. Read `.brain/handover.md` first if there is an unfinished task
3. From `.brain/session.json`, priority:
   - working_on
   - pending_tasks
   - verification. verification
   - decisions_made
4. From `.brain/decisions.json`, only get the entry but also `active` and match the current scope
5. From `.brain/learnings.json`, only get items from repeated failures, incidents, or repeated patterns
6. From `.brain/brain.json`, only get decisions/patterns that match the current scope
7. If memory and repo state conflict -> repo state wins
```

The goal is lightweight continuity: getting the right parts helps resume work, not dragging along monolithic "project memory".

### Summary Template
```
Context recap:
- In progress: [...]
- Important files/changes: [...]
- Pending: [...]
- Risks / assumptions: [...]
- Most reasonable next step: [...]
```

If there is appropriate continuity, add:

```
- Relevant continuity: [decision / blocker / verification / handover note]
```

### Fallback (without `.brain`)
- Scan manifest and key entrypoints: `package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `docs/`, `src/`, `app/`, `README`
- Provide summary from real artifact
- Don't stop just because of lack of memory files

---

## Save Mode (`/save-brain`)

Only write when the user wants to save context or handover.

### What to save
```
Major:
- new modules
- new schema
- new API
- architectural decisions

Minor:
- unfinished bug fix
- next steps
- files being edited
- verification commands already run
```

### Priority data
- `.brain/handover.md` for short handover
- `.brain/session.json` for dynamic state
- `.brain/decisions.json` for decision to be valid according to scope
- `.brain/learnings.json` for repeated failure or reusable pattern
- `.brain/brain.json` only when there is a structural change

### Lightweight Continuity Rule

Save only what's useful for later:
- the decision is still valid
- blocker or risk is not finished
- next steps is actually still open
- verification or command to remember so as not to start over again

Do not save:
- verbose recap just repeats the repo state
- vague conclusion like "almost done"
- memory does not attach scope or next action

### Structured Continuity Capture

When you need to save something more durable than a short handover:

```powershell
python scripts/capture_continuity.py "Checkout rollback must preserve a 1-release compatibility window" `
  --kind decision `
  --scope checkout `
  --evidence "docs/specs/checkout-spec.md" `
  --next "verify old client path in smoke run" `
  --revisit-if "consumer contract changes"
```

Or:

```powershell
python scripts/capture_continuity.py "This regression only surfaces when queue retries run in parallel" `
  --kind learning `
  --scope sync-engine `
  --trigger "3 failed fixes around retry ordering" `
  --evidence "debug report 2026-03-23" `
  --tag retry `
  --tag concurrency
```

Rule:
- `decision`: only save valid things for next time
- `learning`: only stores patterns that have evidence, usually coming from repeated failures or incidents
- Repo state still wins if there is a conflict

If continuity and repo state are different and difficult to fix, read `references/failure-recovery-playbooks.md`.

### Session JSON suggestions
```json
{
  "updated_at": "",
  "working_on": { "feature": "", "task": "", "status": "", "files": [] },
  "pending_tasks": [],
  "recent_changes": [],
  "verification": [],
  "decisions_made": []
}
```

---

## Handover Mode

Used when a user requests or a long/high-risk task needs to be transferred.

```
HANDOVER
- In progress: [feature/task]
- Completed: [list]
- Remaining: [list]
- Important decisions: [list]
- Important files: [list]
- Verification commands already run: [list]
```

Save at `.brain/handover.md` if the user wants to save.

---

## Activation Announcement

```
Forge: session | restore/save context from the repo first, `.brain` second
```
