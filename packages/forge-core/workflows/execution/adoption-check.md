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

## Required Output

- target environment or audience
- observed adoption or usage signal
- early regression or friction notes
- next action if adoption is weak or noisy
- whether the signal supports the release-readiness claim or challenges it

## Verification

- the check records a concrete post-deploy signal
- weak adoption or friction remains visible instead of being folded into deploy notes
- the result can be consumed by `release-readiness` without reconstructing context from chat memory
