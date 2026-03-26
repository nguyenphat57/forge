---
name: next
type: flexible
triggers:
  - natural-language request for the next action
  - optional alias: /next
quality_gates:
  - Repo state inspected before advice
  - One concrete next step only
  - Codex wrapper stays thin on top of the core navigator
---

# Next - Codex Operator Wrapper

> Goal: provide a clear next step for the Codex without creating an additional ceremony.

## Process

1. Resolve with:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

2. Short answer:
   - main next step
   - why this is the right step
   - up to 2 alternatives if needed

## Activation Announcement

```text
Forge Codex: next | one concrete next step from repo state
```
