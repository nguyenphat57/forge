---
name: next
type: flexible
triggers:
  - natural-language request for the next action
  - optional alias: /next
quality_gates:
  - Repo state inspected before advice
  - One concrete next step only
  - Codex wrapper stays thin on top of the core navigator
---

# Next - Codex Operator Wrapper

> Muc tieu: dua ra mot buoc tiep theo ro rang cho Codex ma khong tao them ceremony.

## Process

1. Resolve bang:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

2. Tra loi ngan:
   - next step chinh
   - vi sao day la buoc dung
   - toi da 2 lua chon thay the neu can

## Activation Announcement

```text
Forge Codex: next | one concrete next step from repo state
```
