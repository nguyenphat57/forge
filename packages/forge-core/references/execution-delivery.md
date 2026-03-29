# Forge Execution Delivery

> Use this when implementation needs checkpoints, clear ownership, and less drift after `plan` or `architect`.

## Target

- choose the right execution mode before batch coding
- run a process precheck before any behavior-changing edit
- require a quick plan/design approval path for small creative work
- define the execution pipeline and reviewer lane for medium/large or high-risk work
- choose lane tiers instead of pushing every lane to the same capability level
- require `spec-review` before build when boundary or risk is still unclear
- make the execution packet explicit enough to run each slice without guessing
- track progress with short artifacts instead of relying on session memory
- end with a clear completion state instead of vague status language

## Execution Modes

|Mode | Use when | Signals|
|------|----------|--------|
|`single-track` | One primary critical path | High coupling, dense context, boundaries not cleanly separable|
|`checkpoint-batch` | Several sequential steps in the same direction | `done -> next -> blocker` checkpoints can be locked phase by phase|
|`parallel-safe` | Multiple independent slices | Boundaries are clear and each slice can be verified independently|

## Mode Selection Rules

1. `small` -> almost always `single-track`
2. `medium` -> default to `single-track`, but behavior-changing slices should still carry a clean baseline and may need a worktree
3. `large` -> choose a mode explicitly
4. if parallelism might be unsafe, stay on `single-track`
5. if the task has many steps with the same blast radius, prefer `checkpoint-batch`

## Execution Pipelines

Forge does not assume that every host supports true subagents. A `lane` is a logical role:

- if the host supports subagents, lanes can run independently
- if it does not, keep the lanes separate as sequential passes

|Pipeline | Use when | Lanes|
|---------|----------|------|
|`single-lane` | Small or medium low-risk work | `implementer`|
|`implementer-quality` | Medium/large work with clear enough specs but still needing independent quality review | `implementer` -> `quality-reviewer`|
|`implementer-spec-quality` | Large work, or medium/high-risk work gated by `spec-review` | `implementer` -> `spec-reviewer` -> `quality-reviewer`|
|`deploy-gate` | Medium/large deploy or release-sensitive work | `deploy-reviewer` -> `quality-reviewer`|

Rules:
- if `BUILD` includes `spec-review`, default to `implementer-spec-quality`
- `large` work or profiles stronger than `standard` must include at least `quality-reviewer`
- every lane needs its own real input and output

## Lane Model Tiers

Forge uses abstract tiers instead of hard-coding vendor models:

|Tier | Use for|
|------|--------|
|`cheap` | navigation, triage, artifact reading, status formatting|
|`standard` | bounded implementation slices, standard review, day-to-day execution|
|`capable` | high-risk implementation, spec review, release gates, migration/auth/payment review|

Default stance:
- `navigator` -> `cheap`
- `implementer` -> `standard`
- `spec-reviewer` -> `capable`
- `quality-reviewer` -> `standard`
- `deploy-reviewer` -> `standard`

Upgrade rules:
- `large` -> implementation and review lanes lean toward `capable`
- `release-critical`, `migration-critical`, `external-interface`, `regression-recovery` -> upgrade the relevant review lane to `capable`
- do not force every lane to `capable` for a low-risk slice

## Isolation & Reviewer Recommendations

For `large`, `release-critical`, or `high-risk` work, choose from:

|Recommendation | Use when|
|----------------|--------|
|`same-tree` | Clean repo, narrow scope, easy rollback|
|`worktree` | Dirty repo, high-risk change set, or explicit isolation needed|
|`subagent-split` | The host supports subagents and boundaries are clearly separable|
|`independent-reviewer` | The work needs an independent review lane after implementation|

Rules:
- dirty repo + medium/large/high-risk work -> default toward `worktree`
- behavior-changing medium+ work -> default toward a clean baseline and usually a worktree unless the repo is already isolated and clean
- multiple independent slices + host support -> `subagent-split` can be appropriate
- auth/payment/migration/release-critical work -> lean toward `independent-reviewer`
- if the boundary is not justified clearly, do not split the work

## Delegation Packet

If execution chooses `subagent-split` or an independent reviewer lane, the controller must prepare explicit packets instead of forcing every lane to reread the full thread.

```text
Delegation packet:
- Goal: [...]
- Owned files / write scope: [...]
- Allowed reads / shared artifacts: [...]
- Proof before progress: [...]
- Verification to rerun: [...]
- Return contract: [changed files, verification, residual risk]
```

Rules:
- each packet has one write owner
- do not let two lanes edit the same file without a merge plan
- reviewer lanes should review from packet + evidence, not by replaying the implementer's full context
- if the host has no subagents, use the same packet shape to keep sequential passes clean

## Checkpoint Artifact

A short progress artifact should contain:

```text
Execution progress:
- Task: [...]
- Mode: [...]
- Stage: [...]
- Status: [active/completed/blocked]
- Completion state: [in-progress/ready-for-review/ready-for-merge/blocked-by-residual-risk]
- Lane: [navigator/implementer/spec-reviewer/quality-reviewer/deploy-reviewer]
- Model tier: [cheap/standard/capable]
- Proof before progress: [...]
- Done: [...]
- Next: [...]
- Blockers: [...]
- Risks: [...]
```

If the work spans multiple phases or checkpoints, persist it with `scripts/track_execution_progress.py`.

## Execution Packet

Before editing a medium/large slice, the minimum packet should contain:

```text
Execution packet:
- Sources: [plan/spec/design/spec-review]
- Current slice: [...]
- File/surface scope: [...]
- Baseline: [...]
- Proof before progress: [...]
- Out of scope: [...]
- Reopen if: [...]
```

This packet is the bridge between `plan/architect/spec-review` and `build`.

## Stage Exit Criteria

A stage or slice is complete only when:
- its proof has passed
- the relevant boundary has not been breached
- the checkpoint states the next slice or blocker explicitly
- no silent assumptions are being pushed downstream

## Chain Visibility

When work becomes a long-running chain instead of a single checkpoint, use:

```text
Chain status:
- Chain: [...]
- Status: [active/paused/completed/blocked]
- Current stage: [...]
- Completed stages: [...]
- Next stages: [...]
- Active skills: [...]
- Active lanes: [...]
- Lane model assignments: [...]
- Gate decision: [go/conditional/blocked]
- Review iteration: [n/max]
- Blockers: [...]
- Risks: [...]
```

Persist this with `scripts/track_chain_status.py` when:
- the chain has 3+ stages
- many skills are active
- the work must pause/resume cleanly
- multiple lanes need independent visibility

## Bounded Review Loops

Spec-review and review lanes cannot loop forever.

Default rules:
- `spec-review` allows at most `3` `revise` rounds
- exceeding that threshold becomes `blocked` and returns to `plan` or `architect`
- every revision round must name the exact fix, not repeat vague feedback

This keeps execution from degrading into endless review churn.

## Completion States

|State | Meaning|
|-------|--------|
|`in-progress` | Not enough evidence for handoff|
|`ready-for-review` | Implementation is verified and waiting for final review|
|`ready-for-merge` | Use only when scope is small or review is decisively clean|
|`blocked-by-residual-risk` | Risk or blockers are still too large to call the work done|

## Anti-Patterns

- using `parallel-safe` when the boundary is unclear
- coding from "what seems easiest" instead of from the execution packet
- skipping checkpoints on large work and reconstructing status from memory at the end
- using `ready-for-merge` while unverified risk still exists
- handing off with language such as "almost done" instead of a concrete state
