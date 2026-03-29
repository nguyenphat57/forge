---
name: review-pack
type: flexible
quality_gates:
  - Repo-aware checklist generated
  - Security-minded focus included for public release surfaces
---

# Review Pack

## Intent

Generate a repeatable pre-release review pack for a solo dev instead of relying on ad-hoc memory.

## What It Should Include

- findings-first review stance
- core release checklist that still works without a companion
- security-minded checks for public surfaces
- stack-aware checks inferred from repo signals and optional companions
- optional adversarial prompts for higher-risk work

## Examples

- auth flows: session expiry, password handling, access control
- billing flows: webhook signature, idempotency, subscription state transitions
- database changes: migration safety and rollback path

## Rules

- the pack is not the review itself; it prepares the review
- repo-visible signals should be enough to produce a usable pack even when no companion matches
- missing env docs for sensitive features should appear as findings
- adversarial mode should raise the bar instead of repeating the standard checklist

## Verification

- seeded auth or billing env gaps appear in findings
- adversarial profile adds stronger negative-path checks
