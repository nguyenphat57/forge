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

> Mục tiêu: giữ `/help` rõ ràng cho user Antigravity, nhưng vẫn dùng core navigator của Forge.

## Process

1. Resolve bằng:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

2. Trình bày theo kiểu operator-friendly:
   - bạn đang ở đâu
   - hướng chính
   - tối đa 2 lựa chọn khác

## Activation Announcement

```text
Forge Antigravity: help | one clear recommendation from repo state
```
