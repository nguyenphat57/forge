---
name: next
type: flexible
triggers:
  - shortcut: /next
  - user wants the single best next step
quality_gates:
  - One concrete next step, not vague momentum advice
  - Repo-first reasoning stays intact
  - Wrapper stays thin on top of core navigator
---

# Next - Antigravity Operator Wrapper

> Muc tieu: giu `/next` ro rang cho Antigravity va van bat repo-first contract cua core.

## Process

1. Resolve bang:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

2. Tra ve dung 1 next step chinh.

## Activation Announcement

```text
Forge Antigravity: next | one concrete next step from repo state
```
