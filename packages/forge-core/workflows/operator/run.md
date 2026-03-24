---
name: run
type: flexible
triggers:
  - shortcut: /run
  - user asks to run the app, a script, or a verification command
quality_gates:
  - Command actually runs; do not just restate it
  - Report the key output or failure signal
  - End with the next workflow (`test`, `debug`, or `deploy`) when useful
---

# Run - Execute Then Route

> Muc tieu: chay lenh that, doc output that, va chot buoc tiep theo an toan thay vi chi noi "da chay".

<HARD-GATE>
- Khong duoc claim lenh da chay neu chua co output tu command.
- Khong duoc dua ra ket luan release-ready chi tu mot lenh build/run.
- Neu command fail, dung chinh lenh do lam reproduction anchor cho debug.
</HARD-GATE>

## Process

1. Chot command can chay va timeout hop ly.
2. Run bang CLI deterministic:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
```

3. Doc report:
   - `state`
   - `command_kind`
   - `suggested_workflow`
   - output excerpt va warnings
4. Handoff ngan:
   - command da chay
   - output/failure signal chinh
   - workflow tiep theo nen vao

## Output Contract

```text
Da chay: [...]
Tin hieu chinh: [...]
Lam tiep: [...]
```

## Activation Announcement

```text
Forge: run | execute the command, then route from evidence
```
