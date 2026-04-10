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

> Goal: make "save context" and "resume" mean the exact operation they imply. Restore from real artifacts first; persist only the scoped state that should survive the current window.

<HARD-GATE>
- Do not fabricate token usage, context %, or "memory is almost full".
- Do not use `.brain` instead of repo state when the actual source-of-truth is available.
- Do not load all memory if the current scope only needs a smaller slice.
- Do not capture `decision` or `learning` if it does not have evidence, is not durable enough, or does not have a clear scope attached.
</HARD-GATE>

## Modes

|Triggers | Mode | Action|
|---------|------|-----------|
|`/recap`, `/recap full`, `/recap deep`, "continue", "resume", "restore context" | **Restore** | Run `python scripts/session_context.py resume ...` to rebuild context from repo/doc/plan/.brain|
|`/save-brain`, "save context", "save progress" | **Save** | Run `python scripts/session_context.py save ...` to persist the current task snapshot into `.brain/session.json`|
|Explicit handover request | **Handover** | Create concise transfer notes|

---

## Operating Rules

- Global preferences live in adapter-global split state: canonical fields in `state/preferences.json`, adapter extras in `state/extra_preferences.json`, and only fall back to `.brain/preferences.json` for legacy workspaces that still need migration.

- Repo-first: priority `git status`, changed files, docs, plans, task notes.
- Prefer `.forge-artifacts/workflow-state/<project>/latest.json` when trackers have already recorded execution, chain, or UI progress.
- `.brain` is opt-in: only read/write when the user requests or handover really reduces risk.
- Do not make `/save-brain` a mandatory end-of-task ritual.
- If you have memory, read according to the smallest scope enough to use: global -> module -> current task, do not load it everywhere.

---

## Restore Mode (`/recap`)

When the user says `resume`, `continue`, or `restore context`, treat that as an explicit restore request, not as a loose recap ritual.

Primary entrypoint:

```powershell
python scripts/session_context.py resume --workspace <workspace> --format json
```

In the host there is an equivalent shortcut:
- `/recap` -> quick restore
- `/recap full` -> restore more extensively if the host supports it
- `/recap deep` -> restore more deeply if the host supports it

### Load Order
```
1. docs/plans/, docs/specs/, open task notes
2. git status / changed files / recent commits (if git exists)
3. `.forge-artifacts/workflow-state/<project>/latest.json` when execution, chain, or UI trackers have already persisted state
4. Adapter-global split preferences state (`state/preferences.json` + `state/extra_preferences.json`) via `python scripts/resolve_preferences.py --workspace <workspace> --format json`
5. .brain/handover.md
6. .brain/session.json
7. .brain/decisions.json
8. .brain/learnings.json
9. .brain/brain.json
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

Do not dump the raw preference schema to the user unless they explicitly ask for it. The useful continuity signal is the resolved style, not the raw schema.

### Scope-Filtered Continuity

When `.brain` has enough data, drag only the relevant part:

```text
1. Determine the current scope: feature, module, subsystem, or file cluster
2. Read `.forge-artifacts/workflow-state/<project>/latest.json` first when the repo already has a persisted execution/chain/UI slice
3. Read `.brain/handover.md` first if there is an unfinished task beyond the tracked slice
4. From `.brain/session.json`, priority:
   - working_on
   - pending_tasks
   - verification
   - decisions_made
5. From `.brain/decisions.json`, only pull entries that still match the current scope and remain valid or resume-relevant
6. From `.brain/learnings.json`, prefer repeated-failure patterns, incidents, or reusable lessons that can change the next step
7. From `.brain/brain.json`, only get decisions/patterns that match the current scope
8. If memory and repo state conflict -> repo state wins
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
- Scan manifest and key entry points: `package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `docs/`, `src/`, `app/`, `README`
- Provide summary from real artifact
- Do not stop just because memory files are missing
- If repo state alone is enough to rebuild the next step, `resume` should still succeed from repo state.

---

## Save Mode (`/save-brain`)

Only write when the user explicitly wants to save context or handover.

When the user says `save context`, perform a real session save:

```powershell
python scripts/session_context.py save --workspace <workspace> --format json
```

Add focused flags when the current slice needs them:

```powershell
python scripts/session_context.py save --workspace <workspace> `
  --task "Finish checkout retry slice" `
  --file "src/checkout.ts" `
  --pending "Re-run checkout browser QA" `
  --verification "pytest tests/test_checkout.py -k retry"
```

Meaning:
- `save context` -> persist `.brain/session.json`
- `handover` -> persist `.brain/session.json` and refresh `.brain/handover.md`
- `resume` -> restore from repo state, workflow-state, `.brain/session.json`, and `.brain/handover.md`

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
- `.brain/decisions.json` for decisions that remain valid within the current scope
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
  "decisions_made": [],
  "risks": [],
  "blockers": []
}
```

---

## Handover Mode

Used when a user requests or a long/high-risk task needs to be transferred.

Primary entrypoint:

```powershell
python scripts/session_context.py save --workspace <workspace> --write-handover --format json
```

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

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: session`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.
