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

> Goal: provide a clear Antigravity handover surface on top of the Forge session contract.
> Deprecated compatibility alias for one stable line. Prefer natural-language `handover` requests.

## Process

1. Enter `workflows/execution/session.md` in handover mode.
2. Summarize:
   - what is in progress
   - what is complete
   - what remains
   - important files
   - verification already run
3. Emit a deprecation warning that points users to natural-language `handover`.

## Activation Announcement

```text
Forge Antigravity: handover | concise transfer, not a second recap workflow
```
