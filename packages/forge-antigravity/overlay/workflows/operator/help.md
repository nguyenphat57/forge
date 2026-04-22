---
name: help
type: flexible
triggers:
  - user feels stuck or asks what to do next
quality_gates:
  - Repo state inspected before giving advice
  - One primary recommendation plus at most two alternatives
  - Antigravity wrapper stays thin on top of core navigator
---

# Help - Antigravity Operator Wrapper

> Goal: keep help requests clear for Antigravity users while still using Forge's core navigator.

## Process

1. Resolve using:

If the repo is Forge itself or multiple valid directions are available, use `references/target-state.md` as the policy tie-break before answering.

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

2. Present the result in an operator-friendly format:
   - current state
   - primary direction
   - at most two alternatives

## Activation Announcement

```text
Forge Antigravity: help | one clear recommendation from repo state
```
