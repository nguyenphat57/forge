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

> Mục tiêu: đưa ra một bước tiếp theo rõ ràng cho Codex mà không tạo thêm ceremony.

## Process

1. Resolve bằng:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

2. Trả lời ngắn:
   - next step chính
   - vì sao đây là bước đúng
   - tối đa 2 lựa chọn thay thế nếu cần

## Activation Announcement

```text
Forge Codex: next | one concrete next step from repo state
```
