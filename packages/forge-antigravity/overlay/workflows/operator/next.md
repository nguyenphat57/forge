---
name: next
type: flexible
triggers:
  - user wants the single best next step
quality_gates:
  - One concrete next step, not vague momentum advice
  - Repo-first reasoning stays intact
  - Wrapper stays thin on top of core navigator
---

# Next - Antigravity Operator Wrapper

> Goal: keep next-step requests clear for Antigravity users while preserving the core repo-first contract.

## Process

1. Resolve using:

If the repo is Forge itself and multiple next moves are plausible, use `docs/current/target-state.md` as the policy tie-break before choosing the main step.

```powershell
python commands/resolve_help_next.py --workspace <workspace> --mode next
```

2. Return exactly one primary next step.

## Activation Announcement

```text
Forge Antigravity: next | one concrete next step from repo state
```
