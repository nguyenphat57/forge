---
name: forge-systematic-debugging
description: Use when the task involves a bug, regression, failing test, error, unexpected behavior, or prompt/agent behavior fix.
---

# Forge Systematic Debugging

<EXTREMELY-IMPORTANT>
**REQUIRED GATE:** Use this before proposing or implementing fixes for bugs or unexpected behavior.

```text
NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST
```

**If you have not completed Phase 1, you do not know enough to patch safely.**
</EXTREMELY-IMPORTANT>

## Use When

- Bug, regression, failing test, error log, stack trace, flaky behavior, or unexpected output.
- The user says fix, debug, regression, broken, failing, not working, or prompt bug.
- You are tempted to patch based on a likely cause.
- A test is failing but it is not yet clear why.
- Review feedback identifies a defect but not its root cause.

## Do Not Use When

- The request is a new feature or design change; use `forge-brainstorming`.
- The user only asks for a static explanation and no fix is being attempted.
- The issue is already root-caused with fresh evidence and only needs planned execution.

## Real-World Impact

Thirty minutes of evidence gathering is usually cheaper than three hours of patch churn, stack-up fixes, and new symptoms.

Random fixes waste time, hide the real failure boundary, and teach the wrong lesson to the codebase. Systematic debugging is how you move from "something is wrong" to "this boundary fails for this reason."

## The Four Phases

**You must complete each phase before moving to the next.**

### Phase 1: Root Cause

1. Read the actual error, logs, trace, output, or failing check carefully.
2. Reproduce consistently, or name the missing reproduction gap.
3. Check recent changes, config differences, new dependencies, and environment deltas.
4. Gather evidence at boundaries instead of guessing inside the deepest stack frame.
5. Trace data flow backward until the bad value, missing state, or incorrect assumption originates.

#### Read Error Messages Carefully

- Read the actual error text, not just the headline failure.
- Read stack traces fully enough to identify the first concrete failing boundary.
- Record line numbers, file paths, error codes, and the exact failing command or user action.
- Warnings, stderr, and harness output often explain what changed before the visible failure.

#### Reproduce Consistently

- Write the shortest reliable repro you can.
- If the failure is flaky, name the instability explicitly instead of rounding it down to "works on my machine."
- If you cannot reproduce locally, gather the best available remote proof: CI logs, saved artifacts, traces, screenshots, or captured requests.
- "Almost reproducible" is still a gap. Name the gap before forming a fix.

#### Check Recent Changes

- Read the recent diff, not just the bug report.
- Check config, dependency, environment, seed data, and generated-file changes, not only source code.
- If the issue appeared after a refactor, compare the old and new control flow side by side.
- If nothing obvious changed, verify that assumption with actual history instead of memory.

#### Trace Data Flow Backward

- Start at the visible failure and walk backward to the source of the bad value, missing state, or broken invariant.
- Prefer boundary evidence over stepping deeper into implementation detail too early.
- If the stack trace points to a symptom layer, keep tracing until you find where the wrong assumption entered the system.
- Fix at the origin when possible. Guard at the boundary when the origin cannot be controlled.
- For deep call-chain failures, load `references/debugging/root-cause-tracing.md`.

### Phase 2: Pattern Analysis

1. Find similar working code or a nearby working path.
2. Compare broken and working flows step by step.
3. Read relevant reference code or config completely, not selectively.
4. Identify dependencies, assumptions, state transitions, and environment requirements.
5. Write down the differences that could plausibly matter instead of trusting instinct.

### Phase 3: Hypothesis And Test

1. State one concrete hypothesis: what is wrong, where, and why.
2. State the evidence needed to confirm or kill that hypothesis.
3. Change one variable at a time.
4. Instrument only enough to answer the current hypothesis.
5. If the hypothesis fails, discard it and form a new one. **Do not stack guesses.**

#### When You Do Not Know

- **Say what you do not understand yet.**
- Convert uncertainty into a concrete question, comparison, or diagnostic step.
- Ask for targeted help only after summarizing the current evidence packet.
- Never hide uncertainty behind a patch proposal.

### Phase 4: Fix And Verify

1. Prefer a failing test or deterministic reproduction before editing.
2. Fix the root cause, not the nearest symptom.
3. Rerun the exact reproduction or proof that exposed the bug.
4. Add boundary or broader checks when blast radius exists.
5. Report root cause, fix, proof, and residual risk separately.

#### If Three Fixes Fail, Reset The Lens

- **Three failed fixes in one lane usually means the investigation model is wrong, not that you need a fourth guess.**
- Re-open Phase 1 with the new evidence and question the architecture, state model, or ownership boundary.
- If each attempted fix reveals a different shared-state problem, **stop patching** and name the deeper design issue.
- Discuss the change in lens before continuing if the work may expand into redesign.
- If the root cause is invalid data crossing layers, load `references/debugging/defense-in-depth.md` before deciding the final guard shape.

## Multi-Component Evidence Gathering

When the failure may cross multiple components, gather proof at every boundary before choosing a fix.

For each component boundary:

- Log or inspect what data enters.
- Log or inspect what data exits.
- Verify config or environment propagation.
- Check state transitions at that boundary.
- Use one run to reveal where the chain breaks.

Typical chains include:

- CI -> build -> signing
- CLI -> operator wrapper -> script -> artifact
- UI -> API -> service -> database
- prompt -> bootstrap -> skill selection -> execution guard

The goal is not "more logs." The goal is evidence showing which layer is wrong.

For each chain:

1. Mark the expected boundary contract first.
2. Capture one run with enough evidence to compare expectation vs reality.
3. Stop once you know which boundary diverges; then investigate that layer deeply.
4. Remove or reduce instrumentation after you have the answer.

If the failure is flaky, async, or timing-sensitive, load `references/debugging/condition-based-waiting.md` before increasing sleeps or timeouts.

## Root-Cause Packet

Record:

- Reproduction steps or missing reproduction gap
- Actual error or failing signal
- Suspected boundary
- Recent change or comparison target
- Current hypothesis
- Evidence gathered
- Verification method for the eventual fix

Good packets are short but concrete. Another engineer should be able to read the packet and understand what failed, where the uncertainty still is, and what proof will close the loop.

## Stall Rules

Stop and escalate when:

- 2-3 hypotheses fail without real progress.
- 3 attempted fixes fail or create new symptoms.
- The bug crosses many boundaries without a clear owner.
- Reproduction is unstable and the gap remains unnamed.
- You are tempted to make a "quick patch" just to see what happens.

When stalled, **summarize the evidence, name what is still unknown, and either change lens or ask for targeted help.**

## Human Signals You Are Guessing

If your partner says things like:

- "Is that actually happening?"
- "What evidence do we have?"
- "Will that tell us where it breaks?"
- "Stop guessing."
- "We already tried that."

Treat those as signals that your debugging loop has drifted. **Return to Phase 1 and tighten the evidence packet.**

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "Let us try changing X first." | Guessing is not debugging. |
| "Fix quickly and investigate later." | Symptom fixes preserve the wrong pattern. |
| "The stack trace already tells me enough." | The first visible failure is not always the root cause. |
| "Manual clicking is close enough to reproduction." | Reproduction must be repeatable or the gap must be named. |
| "Log everywhere." | Instrumentation must answer the current hypothesis. |
| "The bug spans too many systems to debug properly." | That is exactly when boundary-by-boundary evidence matters. |
| "I already tried a few fixes, so one more is fine." | Multiple failed fixes are a signal to reset the investigation. |
| "The failing test is flaky, so I cannot use it." | First debug the flake or stabilize the repro; do not bypass proof. |

## Quick Reference

| Phase | Focus | Success signal |
| --- | --- | --- |
| Phase 1 | Error, repro, history, boundaries | You can explain what failed and where the wrong state begins. |
| Phase 2 | Working-vs-broken comparison | You know which differences plausibly matter. |
| Phase 3 | Single hypothesis and targeted proof | One hypothesis is confirmed or decisively killed. |
| Phase 4 | Minimal fix and rerun | The original failure is resolved with fresh proof. |

## Supporting References

Load these only when the problem shape needs them:

- `references/debugging/root-cause-tracing.md` for deep stack traces, bad values, wrong paths, state pollution, or unclear origin.
- `references/debugging/defense-in-depth.md` after root cause shows invalid state crossed multiple trust boundaries.
- `references/debugging/condition-based-waiting.md` for flaky, async, UI, event, process, or timing-related failures.

## When The Root Cause Is External Or Environmental

Sometimes the correct answer is that the defect lives in an external dependency, unstable environment, or timing window you do not control directly.

That still requires process:

- show the evidence proving the external boundary is the failing source
- implement the right local response: retry, timeout, validation, fallback, guardrail, or better error reporting
- capture what remains unverified and what monitoring would tighten confidence later

**Do not use "it is probably environmental" as a shortcut around investigation.**

## Integration

- Called by: the Forge bootstrap for bug, regression, failure, and unexpected-behavior prompts; also by `forge-receiving-code-review` and `forge-executing-plans` when proof fails unexpectedly.
- Calls next: `forge-test-driven-development` once root cause is known and the fix is harnessable, or `forge-writing-plans` if the fix needs a multi-step change.
- Pairs with: `forge-session-management` for resume and evidence restore, `forge-verification-before-completion` for final claims, and `forge-brainstorming` when investigation reveals a design problem rather than a defect.

## Output

Report:

- Reproduction
- Root cause
- Fix
- Proof
- Residual risk

Shared scripts and references live in the installed Forge orchestrator bundle.
