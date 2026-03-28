---
name: next
type: flexible
triggers:
  - shortcut: /next
  - user asks for the next best action
quality_gates:
  - Next step is concrete and anchored to repo state
  - Recommendation does not expand scope
  - Fallback stays actionable when context is weak
---

# Next - Concrete Next-Step Navigator

> Goal: lock in a specific, short, and safe next step based on the current repo state.

<HARD-GATE>
- Do not give vague next steps like "continue doing".
- Do not propose new scopes if the state repo does not support it.
- Do not include more than one main next step. Alternatives are secondary.
</HARD-GATE>

## Process

1. Inspect workspace state:
   - persisted workflow state under `.forge-artifacts/workflow-state/<project>/latest.json` when execution, chain, UI, run, or quality-gate artifacts are available
   - active plan/spec
   - current working tree changes
   - session or handover artifacts if any
2. Resolve with:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

3. Returns:
   - current focus
   - specific next step
   - Maximum 1-2 alternatives when needed

## Output Contract

```text
Current focus: [...]
Next step: [...]
If you need to change direction:
- [...]
```

## Activation Announcement

```text
Forge: next | one concrete step from repo state
```
