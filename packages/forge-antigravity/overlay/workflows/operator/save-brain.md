---
name: save-brain
type: flexible
triggers:
  - shortcut: /save-brain
  - user asks to save continuity or lightweight handover
quality_gates:
  - Saved continuity is scoped and evidence-backed
  - Save flow stays lightweight
  - Wrapper reuses core session save rules
---

# Save-Brain - Antigravity Continuity Wrapper

> Mục tiêu: giữ `/save-brain` cho user quen AWF/Antigravity nhưng không biến nó thành memory ritual bắt buộc.

## Process

1. Vào `workflows/execution/session.md` theo save mode.
2. Chỉ lưu:
   - next step còn mở
   - verification đã chạy
   - risk/blocker đang mở
3. Nếu cần structured continuity, dùng `scripts/capture_continuity.py`.

## Activation Announcement

```text
Forge Antigravity: save-brain | capture only durable continuity
```
