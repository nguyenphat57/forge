---
name: change
type: execution
triggers:
  - medium or large work needs a durable artifact trail
  - user wants a change folder before implementation
quality_gates:
  - Create change artifacts before implementation
  - Record status and verification updates durably
  - Archive completed changes back into project knowledge
---

# Change - Durable Medium And Large Work Artifacts

> Goal: make medium and large work survive after the chat window is gone.

## Process

1. Start a change:

```powershell
python scripts/change_artifacts.py start "feature summary" --workspace <workspace>
```

2. Update status as implementation and verification move forward.
3. Archive the change once the slice is shipped or intentionally paused.

## Required Artifacts

- `proposal.md`
- `design.md`
- `tasks.md`
- `status.json`
- `verification.md`
