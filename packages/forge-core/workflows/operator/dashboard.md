---
name: dashboard
type: flexible
quality_gates:
  - Workspace state summarized from durable artifacts
  - Active verification and release signals surfaced
---

# Dashboard - Solo-Dev Work State

## Intent

Render one terminal-first snapshot of the current workspace so the solo dev does not need to dig through `.brain`, plans, change artifacts, quality gates, canaries, and runtime tool state manually.

## Use When

- returning to an existing repo after a break
- checking whether the current slice is blocked, review-ready, or still active
- checking whether release signals are missing before shipping

## Inputs

- workspace root
- `.brain/session.json`
- `.brain/decisions.json`
- `.brain/learnings.json`
- latest plan/spec
- codebase map if present
- workflow-state or legacy workflow artifacts
- active change artifact if present
- latest release-doc sync, workspace canary, and release-readiness reports if present

## Output

The dashboard should show:

- current stage
- current focus
- next workflow
- recommended action
- latest verification
- continuity counts
- companion matches
- runtime tool health
- release-state hints

## Hard Rules

- prefer durable artifacts over chat memory
- surface missing evidence explicitly instead of smoothing it over
- do not say a slice is ready when the latest quality gate or release signal disagrees

## Verification

- dashboard reflects a real workspace without manual editing
- dashboard can run on a workspace with only partial artifacts
- release state appears when release-doc sync or canary artifacts exist

## How To Run

```powershell
python scripts/dashboard.py --workspace <workspace> --persist --format json
```

Persisted artifacts:
- `.forge-artifacts/dashboard/latest.json`
- `.forge-artifacts/dashboard/history/`

After running:
- use `next` if the dashboard shows a concrete active slice
- use `doctor` if the dashboard suggests runtime or workspace health is suspect
- use `map-codebase` if the repo is still effectively unscoped
