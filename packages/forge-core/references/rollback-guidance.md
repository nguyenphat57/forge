# Forge Rollback Guidance

> Dung khi can mot rollback plan an toan, khong blind-execute.

## Canonical Script

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high --failure-signal "writes failing after migration"
```

## Contract

- Chot rollback scope
- Chot customer impact va data risk
- Chon strategy an toan nhat
- Tra ve suggested workflow tiep theo va verification checklist

## Boundary

- Core chi lap ke hoach rollback.
- Adapter co the them UX wrapper, nhung khong duoc bo qua warning data-risk hay rollback-scope gate.
