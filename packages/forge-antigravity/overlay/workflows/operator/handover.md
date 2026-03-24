---
name: handover
type: flexible
triggers:
  - shortcut: /handover
  - explicit handoff request
quality_gates:
  - Handover stays concise
  - Key files, verification, and next step are captured
  - Wrapper reuses core session handover contract
---

# Handover - Antigravity Session Wrapper

> Mục tiêu: cho Antigravity một bề mặt handover rõ ràng trên cùng contract session của Forge.

## Process

1. Vào `workflows/execution/session.md` theo handover mode.
2. Tóm tắt:
   - đang làm gì
   - đã xong gì
   - còn lại gì
   - files quan trọng
   - verification đã chạy

## Activation Announcement

```text
Forge Antigravity: handover | concise transfer, not a second recap workflow
```
