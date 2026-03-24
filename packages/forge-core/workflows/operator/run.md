---
name: run
type: flexible
triggers:
  - shortcut: /run
  - user asks to run the app, a script, or a verification command
quality_gates:
  - Command actually runs; do not just restate it
  - Report the key output or failure signal
  - End with the next workflow (`test`, `debug`, or `deploy`) when useful
---

# Run - Execute Then Route

> Mục tiêu: chạy lệnh thật, đọc output thật, và chốt bước tiếp theo an toàn thay vì chỉ nói "đã chạy".

<HARD-GATE>
- Không được claim lệnh đã chạy nếu chưa có output từ command.
- Không được đưa ra kết luận release-ready chỉ từ một lệnh build/run.
- Nếu command fail, dùng chính lệnh đó làm reproduction anchor cho debug.
</HARD-GATE>

## Process

1. Chốt command cần chạy và timeout hợp lý.
2. Run bằng CLI deterministic:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Đọc report:
   - `state`
   - `command_kind`
   - `suggested_workflow`
   - `error_translation` nếu command fail hoặc timeout
   - output excerpt và warnings
4. Handoff ngắn:
   - command đã chạy
   - output/failure signal chính
   - workflow tiếp theo nên vào

## Output Contract

```text
Đã chạy: [...]
Tín hiệu chính: [...]
Làm tiếp: [...]
```

## Activation Announcement

```text
Forge: run | execute the command, then route from evidence
```
