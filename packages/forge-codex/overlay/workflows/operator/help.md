---
name: help
type: flexible
triggers:
  - natural-language request for guidance or what to do next
  - optional alias: /help
quality_gates:
  - Repo state inspected before advice
  - One primary recommendation plus at most two alternatives
  - Codex wrapper stays thin on top of the core navigator
---

# Help - Codex Operator Wrapper

> Mục tiêu: giữ `help` tự nhiên cho Codex, nhưng vẫn dùng core navigator của Forge.

## Process

1. Resolve bằng:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

2. Trả lời ngắn gọn theo kiểu Codex:
   - bạn đang ở đâu
   - bước nên làm tiếp
   - tối đa 2 lựa chọn khác nếu cần

## Activation Announcement

```text
Forge Codex: help | repo-first guidance, natural-language first
```
