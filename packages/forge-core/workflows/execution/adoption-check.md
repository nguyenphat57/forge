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
