---
name: help
type: flexible
triggers:
  - shortcut: /help
  - user feels stuck or asks what to do next
quality_gates:
  - Repo state inspected before giving advice
  - One primary recommendation plus at most two alternatives
  - No recap theater or save-memory ritual
---

# Help - Contextual Operator Guidance

> Mục tiêu: đưa ra hướng dẫn ngắn, đúng ngữ cảnh, và dựa trên repo state thật sự có sẵn.

<HARD-GATE>
- Không được gợi ý `/recap` hoặc `/save-brain` như reflex.
- Không fabricate current state nếu repo/artifact chưa xác nhận.
- Không đưa hơn 1 hướng chính và tối đa 2 lựa chọn thay thế.
</HARD-GATE>

## Process

1. Đọc repo state hữu ích nhất:
   - `git status`
   - plan/spec docs gần nhất
   - `.brain/session.json` hoặc `.brain/handover.md` nếu có
2. Resolve bằng:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

3. Trả lời ngắn gọn:
   - Bạn đang ở đâu
   - Làm tiếp gì là tốt nhất
   - Tối đa 2 lựa chọn thay thế nếu cần

## Output Contract

```text
Bạn đang ở: [...]
Làm tiếp: [...]
Lựa chọn khác:
- [...]
- [...]
```

## Activation Announcement

```text
Forge: help | repo-first guidance, no recap theater
```
