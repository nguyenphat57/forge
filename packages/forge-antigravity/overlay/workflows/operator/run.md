---
name: run
type: flexible
triggers:
  - shortcut: /run
  - user asks to run the app, a script, or a verification command
quality_gates:
  - Command actually runs; do not just restate it
  - Report the key output or failure signal
  - Wrapper stays thin on top of core run guidance
---

# Run - Antigravity Operator Wrapper

> Goal: keep `/run` clear for Antigravity users, while still routing from the real output of core `run_with_guidance.py`.

## Process

1. Lock the command.
2. Execute using:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Report:
   - command that ran
   - key signal
   - next workflow

## Activation Announcement

```text
Forge Antigravity: run | execute first, route from evidence second
```
