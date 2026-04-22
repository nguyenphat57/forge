# Condition-Based Waiting

Use this when a failure involves async behavior, flaky tests, polling, UI readiness, background jobs, file creation, server startup, or any test that waits with a guessed delay.

Core rule: wait for the condition you need, not for an amount of time you hope is enough.

## When To Load This Reference

- A test uses `sleep`, `setTimeout`, fixed delays, or manual waiting.
- A check passes locally but flakes in CI or under parallel load.
- A file, event, network response, DOM state, process output, or background job may not be ready yet.
- The current fix idea is "increase the timeout."
- You need to distinguish real timeout behavior from readiness waiting.

## Replace Delay With Condition

Bad pattern:

```text
wait 500 ms
then assert output exists
```

Better pattern:

```text
wait until output exists, with a timeout that fails clearly
then assert output contents
```

The timeout still exists, but only as a safety cap. The condition is the real contract.

## Common Conditions

| Scenario | Wait for |
| --- | --- |
| Event stream | event with expected type or payload |
| UI readiness | element, text, route, request completion, or disabled/enabled state |
| File output | file exists and content is complete |
| Process startup | port open, health endpoint, pid ready, or expected stdout |
| Background job | state changes to complete/failed with reason |
| Queue or cache | count, key, version, or timestamp reaches expected state |

## Polling Requirements

A condition-based wait must:

- evaluate fresh state each loop
- have a bounded timeout
- fail with a message naming the missing condition
- poll at a reasonable interval
- avoid swallowing the last useful error

## When Fixed Delays Are Acceptable

A fixed delay is acceptable only when the behavior under test is time itself.

Examples:

- debounce interval
- throttle window
- timeout expiry
- retry backoff
- animation duration that is part of the contract

Even then:

- first wait for the trigger condition
- use the smallest justified duration
- document the reason for the delay
- keep the assertion tied to the timed behavior

## Debugging A Flake

1. Identify the guessed wait.
2. Name the real readiness condition.
3. Add temporary diagnostics showing condition progress.
4. Replace the delay with a bounded wait.
5. Prove the failure now reports the missing condition instead of timing out vaguely.

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "Just double the sleep." | This usually hides the race and slows the suite. |
| "It only flakes in CI." | CI is evidence of timing or isolation assumptions. |
| "The async operation should be done by then." | "Should" is not a condition. |
| "Polling is ugly." | A clear bounded wait is better than a magic delay. |
| "The timeout passed once locally." | One local pass does not prove stability. |

Pair this with `debugging/root-cause-tracing.md` when the flaky symptom hides where readiness actually breaks.
