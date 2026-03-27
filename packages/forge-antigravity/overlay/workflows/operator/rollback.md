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

> Goal: keep `/rollback` clear for Antigravity users while maintaining the risk-first contract of core.

## Process

1. Lock the scope: deploy/config/migration/code-change.
2. Resolve using:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
```

3. Return:
   - safest strategy
   - warnings
   - post-rollback verification checklist

## Activation Announcement

```text
Forge Antigravity: rollback | plan the safest recovery, not a blind revert
```
