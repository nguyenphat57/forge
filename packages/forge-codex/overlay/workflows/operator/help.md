---
name: help
type: flexible
triggers:
  - natural-language request for guidance or what to do next
  - optional alias: /help
quality_gates:
  - Repo state inspected before advice
  - One primary recommendation plus at most two alternatives
  - Codex wrapper stays thin on top of the core navigator
---

# Help - Codex Operator Wrapper

> Muc tieu: giu `help` tu nhien cho Codex, nhung van dung core navigator cua Forge.

## Process

1. Resolve bang:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

2. Tra loi ngan gon theo kieu Codex:
   - ban dang o dau
   - buoc nen lam tiep
   - toi da 2 lua chon khac neu can

## Activation Announcement

```text
Forge Codex: help | repo-first guidance, natural-language first
```
