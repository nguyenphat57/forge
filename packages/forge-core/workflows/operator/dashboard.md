---
name: dashboard
type: flexible
triggers:
  - operator asks for a concise workspace status board
  - long-running build or release work needs a quick scan surface
quality_gates:
  - Dashboard is a read model over existing artifacts
  - No invented telemetry or percentage progress
  - Packet state, release state, and next action stay grounded in persisted evidence
---

# Dashboard - Thin Workspace Status View

> Goal: show the current Forge state quickly without replacing packet artifacts, workflow-state, or quality gates.

<HARD-GATE>
- Do not invent progress percentages, LOC counters, or "velocity" metrics.
- Do not let the dashboard become the source of truth for packets or release state.
- If the dashboard and the persisted packet disagree, trust the packet artifact and fix the read model.
</HARD-GATE>

## Use When

- a long-running build chain needs a quick scan of packet status, browser QA pending, or next merge point
- release-tail work needs one glanceable view of tier, gate, and adoption signal
- the operator needs a fast "where am I?" surface before opening the deeper artifacts

## Process

1. Read the latest workflow-state and related persisted artifacts.
2. Render the dashboard with:

```powershell
python scripts/dashboard.py --workspace <workspace>
```

3. If the dashboard reveals a blocker, stale packet, or drift, open the underlying artifact and act there.

## What The Dashboard Should Surface

- current stage and focus
- next workflow and recommended action
- active packets, blocked packets, and review-ready packets when present
- browser QA pending and next merge point when packet state carries them
- latest gate, release tier, and latest adoption signal when release-tail work is active

## Activation Announcement

```text
Forge: dashboard | thin view over packet state and release state
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: dashboard`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.