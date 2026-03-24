---
name: rollback
type: flexible
triggers:
  - natural-language request to undo or roll back a release
  - optional alias: /rollback
quality_gates:
  - Scope and risk are classified first
  - Recovery strategy comes from the core planner
  - Post-rollback verification is stated
---

# Rollback - Codex Operator Wrapper

> Mục tiêu: giữ rollback flow ngắn và risk-first cho Codex, không biến nó thành command ritual.

## Process

1. Resolve bằng core planner:

```powershell
python scripts/resolve_rollback.py --workspace <workspace> --scope deploy --format json
```

2. Trả lời ngắn:
   - scope và risk
   - strategy an toàn nhất
   - verify sau rollback

## Activation Announcement

```text
Forge Codex: rollback | classify scope, then recover safely
```
