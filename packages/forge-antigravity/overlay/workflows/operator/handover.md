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

> Muc tieu: cho Antigravity mot be mat handover ro rang tren cung contract session cua Forge.

## Process

1. Vao `workflows/execution/session.md` theo handover mode.
2. Tom tat:
   - dang lam gi
   - da xong gi
   - con lai gi
   - files quan trong
   - verification da chay

## Activation Announcement

```text
Forge Antigravity: handover | concise transfer, not a second recap workflow
```
