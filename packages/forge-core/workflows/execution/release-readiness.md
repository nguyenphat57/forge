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

## Inputs

- latest quality gate
- latest release-doc sync report
- latest workspace canary report
- rollout readiness from canary runs when available

## Profiles

- `standard`
- `production`

`production` is stricter:

- conditional gates should fail
- docs drift should fail
- missing workspace canary should fail
- missing rollout-readiness data should fail

## Output

- PASS / WARN / FAIL
- blockers
- warnings
- per-check detail
- verdict must remain useful on a repo with no companion active

## Verification

- a clean slice can pass
- production readiness fails for unresolved doc drift or missing hard release evidence
