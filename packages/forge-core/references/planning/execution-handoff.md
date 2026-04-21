# Execution Handoff

`plan` stops before `build` until the user chooses how to execute.

Use this handoff:

```text
Plan complete and saved to `docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
```

Persist this state when recording workflow state:

```text
decision: execution-choice-required
next_action: Choose Subagent-Driven or Inline Execution before build.
```

Valid user choices:
- `Subagent-Driven`: split independent tasks and use delegated workers where available.
- `Inline Execution`: execute serially in the current agent when tasks are small or tightly coupled.

Until one choice is made, `next` should keep focus on `plan`.
