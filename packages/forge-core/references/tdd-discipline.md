# TDD Discipline

Use this reference when a behavioral change has a viable harness and the repo needs the full test-first rule, not just a loose verification reminder.

## Core Rule

```text
RED -> GREEN -> REFACTOR
```

- Write and verify a failing test before implementation code.
- If code was written before RED, delete it and restart from the failing test.
- Delete means delete.
- "Keep as reference" is not an exception. Delete means delete.

## Why Tests-After Is Not Equivalent

- Tests-after asks "what does this code do?"
- Test-first asks "what should this code do?"
- Tests-after can validate the implementation you already drifted into.
- RED first proves the harness can actually catch the missing behavior.

## Minimum Loop

1. Write one failing test or reproduction for the exact behavior change.
2. Run it and confirm it fails for the expected reason.
3. Implement the smallest change that makes it pass.
4. Rerun the same proof plus any required boundary checks.
5. Refactor only while the test stays green.

## When To Escalate

- If there is no viable harness, fall back to the strongest explicit reproduction and say why.
- If the test setup is too painful, treat that as design feedback, not a reason to skip RED.
