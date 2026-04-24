---
name: forge-session-management
description: Use when the user asks to resume, continue, restore context, save context, handover, or apply response personalization.
---

# Forge Session Management

<EXTREMELY-IMPORTANT>
Use this before substantive response when session continuity or personalization may matter.

Preferences restore is an invariant, not a routing choice.
</EXTREMELY-IMPORTANT>

## Use When

- Resume, continue, recap, restore context, where were we.
- Save context, handover, capture continuity.
- Thread start needs response personalization restored.

## Do Not Use When

- The user asks a simple standalone question and no preferences or state are needed beyond bootstrap.
- The task is a bug or feature request without session context; use the relevant process skill first.

## Response Personalization

adapter-global preferences live under:

```text
state/preferences.json
```

Use the installed `forge-customize` owner command when available.
Invoke the `resolve_preferences.py` owner command from sibling skill `forge-customize` with `--workspace <workspace> --format json`.

Apply language, orthography, tone detail, and custom rules before substantive output. Do not expose raw preference schema unless asked.

## Restore Order

1. `.forge-artifacts/workflow-state/<project>/latest.json`
2. Latest docs/plans and docs/specs
3. Git status and changed files
4. `.brain/handover.md`
5. `.brain/session.json`
6. Scoped `.brain/decisions.json` and learnings only when relevant

Repo state wins when artifacts conflict.

## Save / Handover

Use installed orchestrator scripts when available:

```powershell
python commands/session_context.py save --workspace <workspace> --format json
python commands/session_context.py save --workspace <workspace> --write-handover --format json
```

The session command is owned by `forge-session-management` and reports `owner: "forge-session-management"` in machine-readable output.

Save only useful continuity: current task, pending next step, changed files, verification, durable decisions, blockers.

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "Memory says enough." | Repo state and workflow-state win. |
| "No memory means stop." | Resume from real repo artifacts. |
| "Token percentages are useful." | Do not fabricate telemetry. |

## Integration

- Called by: the Forge bootstrap at thread start and any resume, continue, save, or handover prompt.
- Calls next: the relevant process skill for the restored task, based on actual repo state and artifacts.
- Pairs with: every workflow-state-aware skill, especially `forge-writing-plans`, `forge-executing-plans`, and `forge-verification-before-completion`.

