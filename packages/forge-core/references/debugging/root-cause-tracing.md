# Root-Cause Tracing

Use this when the visible failure is downstream from the real trigger: a bad value appears deep in a stack, a file is written in the wrong place, a command runs in the wrong directory, state disappears between layers, or a failing test only shows the symptom.

Core rule: trace backward until you find where the wrong assumption entered the system. Fixing the symptom layer is allowed only when the true source cannot be controlled, and then the residual risk must be named.

## When To Load This Reference

- The stack trace points at a generic helper rather than the code that made the wrong decision.
- A value is invalid, missing, stale, duplicated, or unexpectedly transformed.
- The same symptom appears from multiple entrypoints.
- You do not know which test, command, request, or agent lane triggered the state.
- A previous patch fixed one surface but the symptom returned elsewhere.

## Tracing Process

1. Capture the visible symptom exactly: command, error, file path, state, output, or user action.
2. Identify the immediate operation that failed.
3. Ask what input made that operation fail.
4. Find the caller that supplied that input.
5. Repeat until you reach the first point where the data became wrong.
6. Fix at the origin when possible; otherwise guard the boundary and explain why.

Do not stop at the first line with an exception. The first visible failure is often only the place where a bad assumption became impossible to ignore.

## Backward Trace Packet

Record a short chain like this:

```text
Visible failure:
- <exact error or bad output>

Immediate operation:
- <function/command/component that failed>

Bad input:
- <value/state/config that made it fail>

Caller chain:
- <caller 1> passed <bad input>
- <caller 2> produced <bad input>
- <entrypoint> accepted or created <bad input>

Root cause:
- <where the wrong assumption entered>

Fix point:
- <source fix, boundary guard, or both>
```

## Instrumentation

Add only enough instrumentation to answer where the bad value originates.

Useful fields:

- current value and expected shape
- caller or stack trace
- working directory and target path
- environment and config source
- request id, session id, stage, or artifact path
- before/after state at a boundary

Place instrumentation before the dangerous operation. In tests, use output that the harness will actually display when the run fails.

## Finding A Polluter

If test pollution or shared state is suspected:

1. Run the smallest reproducing test set.
2. Split the set until the polluter appears or disappears.
3. Check for global state, temp paths, process cwd, env vars, ports, caches, monkeypatches, and generated files.
4. Confirm by running the suspected polluter before the victim.
5. Fix the shared-state leak, not the victim test.

## Stop Conditions

Stop tracing when:

- you have reached the entrypoint that created or accepted the wrong value
- the next step is external and cannot be inspected
- more tracing would require disproportionate instrumentation

If you stop before the origin, say so. Use defense-in-depth at the boundary and keep the residual uncertainty visible.

## Good Fix Shape

A strong root-cause fix usually includes:

- source correction where the wrong value was created
- validation at the first public or cross-component boundary
- a targeted regression test or deterministic repro
- a concise explanation of why the symptom layer was not the root cause

Pair this with `debugging/defense-in-depth.md` when the bad value crossed multiple layers.
