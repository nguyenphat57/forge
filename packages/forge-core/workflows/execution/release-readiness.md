---
name: release-readiness
type: rigid
quality_gates:
  - Quality gate considered
  - Docs sync considered
  - Canary state considered
---

# Release Readiness

## Intent

Aggregate the latest release signals into one explicit readiness verdict.
For solo-profile releases, this is the final release-surface verdict after docs sync, quality gate, and adoption checks.

## Process

1. Read the latest quality gate, release-doc sync, workspace canary, and adoption-check evidence.
2. Select the active profile and note whether the slice is still pre-release or already live.
3. Decide PASS, WARN, or FAIL from the actual evidence, not from the intended release mood.
4. Call out blockers, warnings, and per-check detail in one place.
5. Hand off to `deploy` only when the verdict is defensible.

## Profiles

- `solo-internal`
- `solo-public`
- `standard`
- `production`

`production` is stricter:

- conditional gates should fail
- docs drift should fail
- missing workspace canary should fail
- missing rollout-readiness data should fail

`solo-public` is also stricter than the default path:

- review-pack/self-review evidence should be present for release-sensitive slices
- docs drift should fail, not linger as background noise
- missing adoption-check signal should be called out explicitly if the release already shipped

## Output

- PASS / WARN / FAIL
- blockers
- warnings
- per-check detail
- verdict must remain useful on a repo with no companion active
- if the release is solo-profile and already live, include whether adoption-check supports or contradicts the readiness claim

## Handover

- PASS moves to `deploy`
- live releases should keep `adoption-check` visible as the post-release tail
- FAIL or WARN should point back to `release-doc-sync`, `quality-gate`, or both, depending on the missing evidence

## Follow-Up Packet

When the release is live and adoption is weak or noisy, capture one compact follow-up packet instead of leaving the verdict as a loose note:

- release tier or profile in use
- target environment or audience
- observed adoption signal
- concrete friction or regression
- next action inside Forge, such as `monitor`, `follow-up fix`, `rollback`, or `re-run readiness`

The packet should stay tied to the release-readiness record so later `help` or `next` calls can consume it without reconstructing context from memory.

## Verification

- a clean slice can pass
- production readiness fails for unresolved doc drift or missing hard release evidence

## Response Footer

When this skill is used to complete a task, include this exact English line in a footer block at the end of the response:

`Used skill: release-readiness.`

Keep that footer block as the last block of the response. If multiple skills are used, include one exact `Used skill:` line per unique skill and do not add anything after the footer block.