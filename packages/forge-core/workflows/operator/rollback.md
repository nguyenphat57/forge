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

> Muc tieu: de xuat rollback strategy an toan nhat, khong blind-revert.

<HARD-GATE>
- Khong rollback mu khi chua ro scope va failure signal.
- Khong de xuat migration rollback nhu reflex neu co nguy co mat du lieu.
- Khong bo qua post-rollback verification.
</HARD-GATE>

## Process

1. Chot scope: `deploy`, `config`, `migration`, hoac `code-change`.
2. Chot customer impact, data risk, va rollback artifact.
3. Resolve bang:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high --failure-signal "writes failing after migration"
```

4. Tra ve:
   - recommended strategy
   - immediate action
   - suggested workflow tiep theo
   - verification checklist

## Output Contract

```text
Rollback strategy: [...]
Lam ngay: [...]
Verify sau rollback: [...]
```

## Activation Announcement

```text
Forge: rollback | plan the safest recovery path first
```
