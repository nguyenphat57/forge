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

## Inputs

- latest quality gate
- latest release-doc sync report
- latest workspace canary report
- rollout readiness from canary runs when available
- latest adoption-check signal when the release is already live

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

## Verification

- a clean slice can pass
- production readiness fails for unresolved doc drift or missing hard release evidence
