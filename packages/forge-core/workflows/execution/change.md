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
3. Run `verify-change` before final merge/deploy-quality claims for medium or large build work.
4. Archive the change once the slice is shipped or intentionally paused.

If the work is being tracked in workflow-state, keep the stage status vocabulary explicit: `pending`, `required`, `active`, `completed`, `skipped`, or `blocked`. Attach activation reasons and skip reasons instead of leaving the state implied.

## Required Artifacts

- `proposal.md`
- `design.md`
- `tasks.md`
- `status.json`
- `verification.md`
- `specs/<topic>/spec.md`

## Artifact Check

```powershell
python scripts/verify_change.py --workspace <workspace> --slug <change-slug> --persist --output-dir <workspace>
```

The change folder and workflow-state should agree on which stages are active and why.

## Response Footer

When this skill is used to complete a task, include this exact English line in a footer block at the end of the response:

`Used skill: change.`

Keep that footer block as the last block of the response. If multiple skills are used, include one exact `Used skill:` line per unique skill and do not add anything after the footer block.