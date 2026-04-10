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
   - packet continuity index under `.forge-artifacts/workflow-state/<project>/packet-index.json` when you need low-cost resume context
   - active plan/spec
   - active change artifact or checkpoint artifact when the work is medium+ or already tracked
   - current working tree changes
   - session or handover artifacts if any
   - `references/target-state.md` if working on Forge itself and the next move changes process direction or strictness
2. Resolve with:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

3. Returns:
   - current focus
   - specific next step
   - Maximum 1-2 alternatives when needed

For medium+ slices, the next step usually favors creating or refreshing the durable artifact before more editing when no such artifact is present yet.
For Forge-maintenance work, the next step should not optimize local convenience at the cost of target-state discipline.
For first-run workspaces with weak context, point to the start-here sequence (`doctor` -> `map-codebase`) before speculative implementation.

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

## Response Footer

When this skill is used to complete a task, include this exact English line in a footer block at the end of the response:

`Used skill: next.`

Keep that footer block as the last block of the response. If multiple skills are used, include one exact `Used skill:` line per unique skill and do not add anything after the footer block.