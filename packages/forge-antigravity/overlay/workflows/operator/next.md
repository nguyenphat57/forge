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

> Mục tiêu: giữ `/next` rõ ràng cho Antigravity và vẫn bám repo-first contract của core.

## Process

1. Resolve bằng:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

2. Trả về đúng 1 next step chính.

## Activation Announcement

```text
Forge Antigravity: next | one concrete next step from repo state
```
