---
name: session
type: flexible
triggers:
  - continue/resume/context restore
  - explicit continuity capture request
  - explicit handover request
quality_gates:
  - Context restored or handover note persisted
  - Workspace response preferences resolved when available
  - Scope-filtered continuity used when available
  - Structured continuity capture stays evidence-backed and scoped
---

# Session - Context & Continuity

> Goal: restore context from real artifacts first and capture only durable continuity when the user explicitly asks.

<HARD-GATE>
- Do not invent token usage, context percentages, or fake memory pressure.
- Do not replace repo state with `.brain` when stronger source-of-truth artifacts exist.
- Do not write broad continuity summaries when the active scope only needs a small slice.
- Do not store a decision or learning without evidence, scope, or clear reuse value.
</HARD-GATE>

## Modes

| Trigger | Mode | Action |
|---------|------|--------|
| "continue", "resume", "where were we", "remind me", "pick this back up" | **Restore** | Rebuild context from repo, plans, docs, and scoped `.brain` artifacts |
| "save current progress", "capture continuity", "leave a short note" | **Save** | Write a compact continuity note only if the user wants persistence |
| Explicit handover request | **Handover** | Create a short transfer note with next step and risk |

## Operating Rules

- Resolve adapter-global Forge preferences early through `scripts/resolve_preferences.py` so the recap follows the user's response settings; `--workspace` only keeps legacy `.brain/preferences.json` fallback alive.

- Repo-first: start from `git status`, changed files, plans, specs, and current docs.
- `.brain` is optional support, not the primary source of truth.
- Continuity should stay narrow: current task, active files, next action, verification, and residual risk.
- If memory and repo state conflict, repo state wins.

## Restore Mode

### Load Order

```text
1. docs/plans/, docs/specs/, task notes that match the current scope
2. git status / changed files / recent commits when git exists
3. Codex-global `state/preferences.json` via `python scripts/resolve_preferences.py --workspace <workspace> --format json`
4. .brain/handover.md
5. .brain/session.json
6. .brain/decisions.json
7. .brain/learnings.json
8. .brain/brain.json
```

### Response Personalization

Resolve preferences before writing the recap:

```powershell
python scripts/resolve_preferences.py --workspace <workspace> --format json
```

Use the resolved payload to adapt:
- terminology and explanation depth
- recap verbosity and detail density
- how proactive the proposed next step should be
- pace, feedback sharpness, and personality in phrasing

Apply the style without dumping raw preference fields unless the user asks for them directly.

### Scope-Filtered Continuity

```text
1. Identify the current feature, module, or file cluster
2. Read .brain/handover.md first if the task was left mid-flight
3. From .brain/session.json, prefer:
   - working_on
   - pending_tasks
   - verification
   - decisions_made
4. Pull only active, scope-matching entries from decisions/learnings
5. Ignore stale or broad memory that does not change the next action
```

### Summary Template

```text
Context recap:
- Current focus: [...]
- Important files or artifacts: [...]
- Pending work: [...]
- Risks or assumptions: [...]
- Best next step: [...]
```

## Save Mode

Use this only when the user explicitly wants continuity captured.

### Good payload

- Current task and scope
- Files or artifacts that matter next
- Verification already run
- Residual risk or blocker
- One concrete next step

### Avoid storing

- Long recaps that just restate repo state
- Vague claims like "almost done"
- Broad project memory with no clear reuse

### Structured continuity capture

```powershell
python scripts/capture_continuity.py "Checkout rollback needs one-release compatibility window" `
  --kind decision `
  --scope checkout `
  --evidence "docs/specs/checkout-spec.md" `
  --next "verify old client path in smoke run" `
  --revisit-if "consumer contract changes"
```

```powershell
python scripts/capture_continuity.py "Regression only appears when queue retry runs in parallel" `
  --kind learning `
  --scope sync-engine `
  --trigger "3 failed fixes around retry ordering" `
  --evidence "debug report 2026-03-23" `
  --tag retry `
  --tag concurrency
```

## Handover Mode

```text
HANDOVER
- Current task: [...]
- Done: [...]
- Remaining: [...]
- Important decisions: [...]
- Verification run: [...]
- Next step: [...]
```

Persist to `.brain/handover.md` only when the user wants a durable handoff.

## Activation Announcement

```text
Forge: session | restore from repo first, capture only scoped continuity
```
