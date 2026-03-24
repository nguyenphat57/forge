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

> Muc tieu: giu `/rollback` ro rang cho Antigravity nhung van giu risk-first contract cua core.

## Process

1. Chot scope: deploy/config/migration/code-change.
2. Resolve bang:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
```

3. Tra ve:
   - strategy an toan nhat
   - warnings
   - verification checklist sau rollback

## Activation Announcement

```text
Forge Antigravity: rollback | plan the safest recovery, not a blind revert
```
