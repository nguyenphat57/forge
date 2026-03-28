---
name: run
type: flexible
triggers:
  - natural-language request to run a command, app, or check
  - optional alias: /run
quality_gates:
  - The command actually runs
  - Key output or failure signal is reported
  - The response ends with the next workflow when useful
---

# Run - Codex Operator Wrapper

> Goal: keep `run` natural in Codex, but still route according to evidence from core.

## Process

1. Close the command that needs to be run and have a reasonable timeout.
2. Run using core guidance:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Short summary:
   - command was run
   - main signal
   - next workflow (`test`, `debug`, or `deploy`) if needed

## Activation Announcement

```text
Forge Codex: run | execute, summarize, route from evidence
```
