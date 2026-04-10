---
name: rollback
type: flexible
triggers:
  - shortcut: /rollback
  - user explicitly asks for rollback planning
quality_gates:
  - Rollback scope is stated before action
  - Data-loss risk is called out when relevant
  - Post-rollback verification is part of the recommendation
---

# Rollback - Controlled Recovery Planning

> Objective: proposes the safest rollback strategy, no blind-revert.

<HARD-GATE>
- Do not rollback blindly when the scope and failure signal are unclear.
- Do not recommend migration rollback like reflex if there is a risk of data loss.
- Do not skip post-rollback verification.
</HARD-GATE>

## Process

1. Battery scope: `deploy`, `config`, `migration`, or `code-change`.
2. Close customer impact, data risk, and rollback artifacts.
3. Resolve with:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high --failure-signal "writes failing after migration"
```

4. Returns:
   - recommended strategy
   - immediate action
   - suggested next workflow
   - verification checklist

## Output Contract

```text
Rollback strategy: [...]
Do it now: [...]
Verify after rollback: [...]
```

## Activation Announcement

```text
Forge: rollback | plan the safest recovery path first
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: rollback`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.