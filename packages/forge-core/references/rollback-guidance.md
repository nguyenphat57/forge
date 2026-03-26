# Forge Rollback Guidance

> Use when you need a safe, non-blind-execute rollback plan.

## Canonical Script

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high --failure-signal "writes failing after migration"
```

## Contract

- Close rollback scope
- Close customer impact and data risk
- Choose the safest strategy
- Returns the next suggested workflow and verification checklist

## Boundary

- Core only plans rollback.
- Adapter can add UX wrapper, but cannot ignore data-risk warning or rollback-scope gate.
