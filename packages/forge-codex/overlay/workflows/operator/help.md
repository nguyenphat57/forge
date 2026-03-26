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

> Goal: keep `help` native to Codex, but still use Forge's core navigator.

## Process

1. Resolve with:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

2. Short answer in Codex style:
   - Where are you?
   - next step to take
   - up to 2 other options if needed

## Activation Announcement

```text
Forge Codex: help | repo-first guidance, natural-language first
```
