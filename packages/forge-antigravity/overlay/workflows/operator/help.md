---
name: help
type: flexible
triggers:
  - shortcut: /help
  - user feels stuck or asks what to do next
quality_gates:
  - Repo state inspected before giving advice
  - One primary recommendation plus at most two alternatives
  - Antigravity wrapper stays thin on top of core navigator
---

# Help - Antigravity Operator Wrapper

> Muc tieu: giu `/help` ro rang cho user Antigravity, nhung van dung core navigator cua Forge.

## Process

1. Resolve bang:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

2. Trinh bay theo kieu operator-friendly:
   - ban dang o dau
   - huong chinh
   - toi da 2 lua chon khac

## Activation Announcement

```text
Forge Antigravity: help | one clear recommendation from repo state
```
