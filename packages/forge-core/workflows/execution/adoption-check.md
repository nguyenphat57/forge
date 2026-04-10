---
name: adoption-check
type: rigid
quality_gates:
  - Post-deploy adoption signal recorded
  - Early regressions or friction surfaced explicitly
---

# Adoption Check

## Intent

Record whether a freshly deployed internal or public release is actually landing as expected after rollout.
For solo-profile work, this is the post-release tail that tells you whether the shipped change is being adopted instead of merely deployed.

## Process

1. Identify the target environment or audience.
2. Record a concrete adoption or usage signal.
3. Note early regression or friction without smoothing it over.
4. Decide whether the signal supports or challenges the release-readiness claim.
5. Hand the signal back to `release-readiness` if adoption is weak or noisy.

## Signal Shapes

Keep the recorded signal bounded to one of these concrete shapes:

- `supportive` when the release is clearly being used as intended
- `adoption lag` when usage is slower than expected but not broken
- `confusion` when users are landing on the shipped change but do not understand it
- `regression` when the deployed behavior is causing breakage or churn
- `environment issue` when the problem is in the target environment rather than the release itself

Each shape should map to a direct Forge action:

- `supportive` -> keep the signal visible and continue monitoring
- `adoption lag` -> keep monitoring or tighten follow-up if it persists
- `confusion` -> clarify the release note or operator guidance
- `regression` -> `follow-up fix` or `rollback` as needed
- `environment issue` -> `monitor` and separate the environment from the release contract

## Output

- target environment or audience
- observed adoption or usage signal
- early regression or friction notes
- next action if adoption is weak or noisy
- whether the signal supports the release-readiness claim or challenges it

## Handover

- keep the observed signal attached to the release-tail record
- if adoption is weak, return to `release-readiness` with the concrete friction
- if adoption is strong, keep the support signal visible for later release review

## Verification

- the check records a concrete post-deploy signal
- weak adoption or friction remains visible instead of being folded into deploy notes
- the result can be consumed by `release-readiness` without reconstructing context from chat memory

## Response Footer

When this skill is used to complete a task, include this exact English line in a footer block at the end of the response:

`Used skill: adoption-check.`

Keep that footer block as the last block of the response. If multiple skills are used, include one exact `Used skill:` line per unique skill and do not add anything after the footer block.