---
name: run
type: flexible
triggers:
  - natural-language request to run a command, app, or check
  - optional alias: /run
quality_gates:
  - The command actually runs
  - Key output or failure signal is reported
  - The response ends with the next workflow when useful
---

# Run - Codex Operator Wrapper

> Mục tiêu: giữ `run` tự nhiên trong Codex, nhưng vẫn route theo evidence từ core.

## Process

1. Chốt command cần chạy và timeout hợp lý.
2. Run bằng core guidance:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Tóm tắt ngắn:
   - command đã chạy
   - tín hiệu chính
   - workflow tiếp theo (`test`, `debug`, hoặc `deploy`) nếu cần

## Activation Announcement

```text
Forge Codex: run | execute, summarize, route from evidence
```
