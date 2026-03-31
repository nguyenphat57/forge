---
name: verify-change
type: rigid
triggers:
  - before final quality-gate on medium or large build work
  - when a change needs artifact-vs-implementation evidence, not just test output
quality_gates:
  - Required change artifacts exist
  - Spec delta exists under active change artifacts
  - Verification state is current enough for handoff
  - Residual risk is explicit
---

# Verify Change - Compare Work Against Durable Artifacts

## The Iron Law

```text
NO FINAL MERGE OR DEPLOY CLAIM FROM TEST OUTPUT ALONE WHEN THE CHANGE HAS DURABLE ARTIFACTS
```

`verify-change` is the bridge between:
- the change packet
- the recorded verification state
- the final quality gate

## Use This When

- the work is `medium` or `large`
- `change_artifacts.py start` created a durable change folder
- the slice is about to claim `ready-for-merge`, `done`, or `deploy`
- the workflow-state record needs to be checked against the active change so stage state is not inferred from memory

## What It Checks

- completeness: required artifact set exists
- correctness: packet and status still make sense together
- coherence: proposal, design, tasks, packet, and spec delta still describe the same change
- evidence strength: current verification is strong enough to trust
- residual risk: remaining gaps are explicit
- workflow-state coherence: active stages use the canonical status vocabulary and carry activation or skip reasons

## Required Artifact Shape

```text
.forge-artifacts/changes/active/<slug>/
- proposal.md
- design.md
- implementation-packet.md
- tasks.md
- verification.md
- resume.md
- status.json
- specs/<topic>/spec.md
```

## Deterministic Command

```powershell
python scripts/verify_change.py --workspace <workspace> --slug <change-slug> --persist --output-dir <workspace>
```

## Decision Rules

- `PASS`: artifact spine is complete and the latest verification is strong enough for final gate consumption
- `WARN`: artifacts exist but evidence or residual risk still needs a reviewer to read carefully
- `FAIL`: required artifacts are missing or the change cannot be trusted for final claims

Rule:
- `ready-for-merge`, `done`, and `deploy` should not use `go` at quality gate if the latest `verify-change` is not `PASS`
- if the change is represented in workflow-state, `PASS` also means the workflow-state stage records match the current slice

## Output

```text
Verify change:
- Status: [PASS/WARN/FAIL]
- Decision: [ready/revise/blocked]
- Change: [slug]
- Scores: [completeness/correctness/coherence/evidence_strength/residual_risk]
- Missing artifacts: [...]
- Latest verification: [...]
- Recommendations: [...]
```

If persisted, the artifact should land under:

```text
.forge-artifacts/verify-change/<change-slug>/
```

## Activation Announcement

```text
Forge: verify-change | compare the active change packet against final evidence
```
