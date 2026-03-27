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

> Goal: keep `/save-brain` for users familiar with AWF/Antigravity, without turning it into a mandatory memory ritual.

## Process

1. Enter `workflows/execution/session.md` in save mode.
2. Save only:
   - open next steps
   - verification already run
   - open risks/blockers
3. If structured continuity is needed, use `scripts/capture_continuity.py`.

## Activation Announcement

```text
Forge Antigravity: save-brain | capture only durable continuity
```
