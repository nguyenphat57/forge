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

> Muc tieu: giu `run` tu nhien trong Codex, nhung van route theo evidence tu core.

## Process

1. Chot command can chay va timeout hop ly.
2. Run bang core guidance:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Tom tat ngan:
   - command da chay
   - tin hieu chinh
   - workflow tiep theo (`test`, `debug`, hoac `deploy`) neu can

## Activation Announcement

```text
Forge Codex: run | execute, summarize, route from evidence
```
