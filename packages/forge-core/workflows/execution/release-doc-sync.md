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

## Typical Triggers

- after a feature ship
- before a release readiness pass
- when config, schema, or product surface changed materially

## Required Output

- changed paths
- doc categories already touched
- missing doc coverage
- suggested doc update surfaces
- release profile observed: `solo-internal`, `solo-public`, or other release target

## Rules

- docs drift is allowed to remain a warning, but it must not be hidden
- the rule set must stay repo-visible and stack-agnostic instead of depending on companion-only metadata
- database or migration changes should push attention toward architecture and release notes
- runtime/config changes should push attention toward README or release docs
- product surface changes should push attention toward README, architecture, or plan/spec surfaces
- if the changed surface is release-facing, missing docs are a finding for the release tail, not just an optional note

## Verification

- seeded drift is detected
- a clean path with touched docs passes
