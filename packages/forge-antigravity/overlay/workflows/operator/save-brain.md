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

> Muc tieu: giu `/save-brain` cho user quen AWF/Antigravity nhung khong bien no thanh memory ritual bat buoc.

## Process

1. Vao `workflows/execution/session.md` theo save mode.
2. Chi luu:
   - next step con mo
   - verification da chay
   - risk/blocker dang mo
3. Neu can structured continuity, dung `scripts/capture_continuity.py`.

## Activation Announcement

```text
Forge Antigravity: save-brain | capture only durable continuity
```
