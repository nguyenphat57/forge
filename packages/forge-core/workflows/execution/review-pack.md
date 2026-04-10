---
name: review-pack
type: flexible
quality_gates:
  - Repo-aware checklist generated
  - Security-minded focus included for public release surfaces
---

# Review Pack

## Intent

Generate a repeatable pre-release review pack for a solo dev instead of relying on ad-hoc memory. The pack is the tail that feeds `self-review`, `quality-gate`, and release-facing handoff for `solo-internal` and `solo-public` flows.

## Process

1. Read the changed surface, release profile, and any change artifact or plan.
2. Build a findings-first checklist from repo-visible signals instead of memory.
3. Include security-minded checks for public or release-facing surfaces.
4. Add stack-aware checks when the repo points at a clear runtime or framework.
5. Make the release tail explicit so the next gate does not have to reconstruct it.

## Output

- findings-first review stance
- core release checklist that still works without a companion
- security-minded checks for public surfaces
- stack-aware checks inferred from repo signals and optional companions
- optional adversarial prompts for higher-risk work
- explicit tail ordering: implementation -> review-pack -> self-review -> quality-gate -> release-doc-sync -> release-readiness -> deploy -> adoption-check when the slice is release-sensitive

## Rules

- the pack is not the review itself; it prepares the review
- repo-visible signals should be enough to produce a usable pack even when no companion matches
- missing env docs for sensitive features should appear as findings
- adversarial mode should raise the bar instead of repeating the standard checklist
- if the work is solo-public or otherwise release-sensitive, the pack should call out `review-pack` as a required tail rather than optional reassurance
- if the release is already live, include the doc-sync, readiness, and adoption-check path that follows the pack

## Handover

- feed `self-review` with the completed pack
- carry missing docs coverage into `release-doc-sync`
- carry live-release confidence gaps into `release-readiness` and `adoption-check`

## Verification

- seeded auth or billing env gaps appear in findings
- adversarial profile adds stronger negative-path checks

## Response Footer

When this skill is used to complete a task, include this exact English line in a footer block at the end of the response:

`Used skill: review-pack.`

Keep that footer block as the last block of the response. If multiple skills are used, include one exact `Used skill:` line per unique skill and do not add anything after the footer block.