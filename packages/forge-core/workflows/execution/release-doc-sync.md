---
name: release-doc-sync
type: rigid
quality_gates:
  - Changed release surfaces identified
  - Missing doc coverage reported explicitly
---

# Release-Doc Sync

## Intent

Check whether release-facing docs drifted away from the changed code or config surface.
For solo-profile work, this is the doc gate that keeps `solo-internal` and `solo-public` releases from shipping with hidden knowledge gaps.

## Process

1. Read the changed paths and identify which release profile is in play.
2. Classify the touched docs surfaces and note what already changed with the slice.
3. Report missing coverage explicitly instead of burying it in a warning.
4. Suggest the doc update surfaces that should move next.
5. Hand off the result to `release-readiness`, or to `adoption-check` if the release is already live.

## Output

- changed paths
- doc categories already touched
- missing doc coverage
- suggested doc update surfaces
- release profile observed: `solo-internal`, `solo-public`, or other release target
- whether the missing coverage is a warning or a release-tail finding

## Rules

- docs drift is allowed to remain a warning, but it must not be hidden
- the rule set must stay repo-visible and stack-agnostic instead of depending on companion-only metadata
- database or migration changes should push attention toward architecture and release notes
- runtime/config changes should push attention toward README or release docs
- product surface changes should push attention toward README, architecture, or plan/spec surfaces
- if the changed surface is release-facing, missing docs are a finding for the release tail, not just an optional note

## Handover

- feed unresolved docs drift into `release-readiness`
- if the change is already live, carry the signal into `adoption-check`
- keep missing release-facing docs visible instead of folding them into deploy notes

## Verification

- seeded drift is detected
- a clean path with touched docs passes

## Response Footer

When this skill is used to complete a task, include this exact English line in a footer block at the end of the response:

`Used skill: release-doc-sync.`

Keep that footer block as the last block of the response. If multiple skills are used, include one exact `Used skill:` line per unique skill and do not add anything after the footer block.