---
name: rollback
type: flexible
triggers:
  - shortcut: /rollback
  - user asks for a rollback plan after a release or config failure
quality_gates:
  - Scope and risk are stated before recommending a rollback
  - Verification after rollback is explicit
  - Wrapper stays thin on top of core rollback planner
---

# Rollback - Antigravity Operator Wrapper

> Mục tiêu: giữ `/rollback` rõ ràng cho Antigravity nhưng vẫn giữ risk-first contract của core.

## Process

1. Chốt scope: deploy/config/migration/code-change.
2. Resolve bằng:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
```

3. Trả về:
   - strategy an toàn nhất
   - warnings
   - verification checklist sau rollback

## Activation Announcement

```text
Forge Antigravity: rollback | plan the safest recovery, not a blind revert
```
