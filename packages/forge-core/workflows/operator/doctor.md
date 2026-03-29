---
name: doctor
type: operator
triggers:
  - user asks to diagnose Forge or workspace health
  - user asks why runtime tools or host wiring are not working
quality_gates:
  - Diagnose actual workspace and runtime state before giving remediation
  - Separate blockers from warnings
  - Persist a machine-readable report when possible
---

# Doctor - Environment And Runtime Health

> Goal: tell the user whether Forge, the workspace, and optional runtime tools are actually usable.

## Process

1. Resolve the workspace root.
2. Run:

```powershell
python scripts/doctor.py --workspace <workspace> --format json
```

3. Report:
   - overall status
   - blockers
   - warnings
   - next remediation steps

## Output Contract

```text
Forge Doctor
- Status: PASS | WARN | FAIL
- Workspace: [...]
- Blockers:
  - [...]
- Warnings:
  - [...]
- Remediations:
  - [...]
```
