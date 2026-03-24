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

> Mục tiêu: đề xuất rollback strategy an toàn nhất, không blind-revert.

<HARD-GATE>
- Không rollback mù khi chưa rõ scope và failure signal.
- Không đề xuất migration rollback như reflex nếu có nguy cơ mất dữ liệu.
- Không bỏ qua post-rollback verification.
</HARD-GATE>

## Process

1. Chốt scope: `deploy`, `config`, `migration`, hoặc `code-change`.
2. Chốt customer impact, data risk, và rollback artifact.
3. Resolve bằng:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high --failure-signal "writes failing after migration"
```

4. Trả về:
   - recommended strategy
   - immediate action
   - suggested workflow tiếp theo
   - verification checklist

## Output Contract

```text
Rollback strategy: [...]
Làm ngay: [...]
Verify sau rollback: [...]
```

## Activation Announcement

```text
Forge: rollback | plan the safest recovery path first
```
