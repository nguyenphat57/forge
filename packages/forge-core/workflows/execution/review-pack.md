---
name: review-pack
type: flexible
quality_gates:
  - Lane-aware checklist generated
  - Security-minded focus included for public release surfaces
---

# Review Pack

## Intent

Generate a repeatable pre-release review pack for a solo dev instead of relying on ad-hoc memory.

## What It Should Include

- findings-first review stance
- release checklist
- security-minded checks for public surfaces
- lane-aware checks inferred from repo signals and first-party companions
- optional adversarial prompts for higher-risk work

## Examples

- auth flows: session expiry, password handling, access control
- billing flows: webhook signature, idempotency, subscription state transitions
- database changes: migration safety and rollback path

## Rules

- the pack is not the review itself; it prepares the review
- missing env docs for sensitive features should appear as findings
- adversarial mode should raise the bar instead of repeating the standard checklist

## Verification

- seeded auth or billing env gaps appear in findings
- adversarial profile adds stronger negative-path checks
