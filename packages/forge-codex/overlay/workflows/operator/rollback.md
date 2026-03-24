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

> Muc tieu: giu rollback flow ngan va risk-first cho Codex, khong bien no thanh command ritual.

## Process

1. Resolve bang core planner:

```powershell
python scripts/resolve_rollback.py --workspace <workspace> --scope deploy --format json
```

2. Tra loi ngan:
   - scope va risk
   - strategy an toan nhat
   - verify sau rollback

## Activation Announcement

```text
Forge Codex: rollback | classify scope, then recover safely
```
