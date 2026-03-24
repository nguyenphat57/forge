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

> Muc tieu: giu `/run` ro rang cho Antigravity, nhung van route tu output that cua core `run_with_guidance.py`.

## Process

1. Chot command.
2. Chay bang:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Bao lai:
   - command da chay
   - tin hieu chinh
   - workflow tiep theo

## Activation Announcement

```text
Forge Antigravity: run | execute first, route from evidence second
```
