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

> Goal: give Antigravity a clear handover surface on top of the Forge session contract.

## Process

1. Enter `workflows/execution/session.md` in handover mode.
2. Summarize:
   - what is in progress
   - what is completed
   - what remains
   - important files
   - verification already run

## Activation Announcement

```text
Forge Antigravity: handover | concise transfer, not a second recap workflow
```
