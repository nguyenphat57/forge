# Forge Execution Delivery

> Use when you need to deploy code after `plan`/`architect` in a way that has checkpoints, completion states, and less drift.

## Target

- Choose the correct execution mode before batch coding
- Close execution pipeline and reviewer lane for medium/large or high-risk work
- Choose a lane-based tier model instead of pushing everything to the same capacity level
- Lock `spec-review` before building if boundary/risk is not locked enough
- The execution packet latch is clear enough to execute each slice without guessing
- Track progress using short artifacts that do not rely on session memory
- End with a clear completion state, without using vague language

## Execution Modes

|Mode | When to use | Identification signs|
|------|--------------|--------------------|
|`single-track` | A main critical path | High coupling, thick context, boundary not clear enough to separate|
|`checkpoint-batch` | Many steps are consecutive but still in the same direction | The `done -> next -> blocker` milestone can be locked in short phases|
|`parallel-safe` | Multiple independent slices | Boundary/interface is clear, each slice can be verified separately|

## Rules for mode selection

1. `small` -> almost always `single-track`
2. `medium` -> default `single-track`
3. `large` -> requires choosing a mode
4. If you are not sure whether parallelism is safe -> do not choose `parallel-safe`
5. If the task has many steps but the same blast radius -> prioritize `checkpoint-batch`

## Execution Pipelines

Forge does not assume that every host has real subagents. `Lane` is the logical concept:

- host has subagents -> can run independent lane
- Host does not have subagents -> must still keep separate lanes for each pass

|Pipelines | Use when | Lanes|
|----------|----------|-------|
|`single-lane` | Small or medium low-risk | `implementer`|
|`implementer-quality` | Medium/large has clear enough specs but still needs an independent quality pass | `implementer` -> `quality-reviewer`|
|`implementer-spec-quality` | Build large or medium/high-risk has `spec-review` | `implementer` -> `spec-reviewer` -> `quality-reviewer`|
|`deploy-gate` | Deploy medium/large or release-sensitive | `deploy-reviewer` -> `quality-reviewer`|

Rules:
- `BUILD` has `spec-review` -> defaults to `implementer-spec-quality`
- `large` or stronger profile than `standard` -> must have at least `quality-reviewer`
- Pipeline should not be just for "show"; Each lane must have its own input/output

## Lane Model Tiers

Forge uses an abstract tier, not a hardcode vendor model:

|Tier | Used for|
|------|----------|
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
- `large` -> implement/review lanes leaning towards `capable`
- `release-critical`, `migration-critical`, `external-interface`, `regression-recovery` -> upgrade related review lane to `capable`
- Do not push every lane to `capable` if the task is just a low-risk slice

## Isolation & Reviewer Recommendation

For task `large`, `release-critical`, or `high-risk`, add:

|Recommendation | When to use|
|----------------|--------------|
|`same-tree` | Clean repo, narrow scope, simple rollback|
|`worktree` | Dirty repo, high-risk changes, or need to isolate change set|
|`subagent-split` | Host supports subagents and boundaries clearly enough|
|`independent-reviewer` | Need independent review lane after implementation|

Rules:
- Dirty repo + large/high-risk -> default towards `worktree`
- Multiple independent slices + host support -> can add `subagent-split`
- Auth/payment/migration/release-critical -> leaning towards `independent-reviewer`
- If you don't justify the boundary clearly, don't divide the subagent

## Delegation Packet

If execution chooses `subagent-split` or a truly independent reviewer lane, the controller must prepare enough packets for each lane instead of forcing the lane to re-read the entire thread:

```text
Delegation packets:
- Goal: [...]
- Owned files / write scope: [...]
- Allowed reads / shared artifacts: [...]
- Proof before progress: [...]
- Verification to rerun: [...]
- Return contract: [changed files, verification, residual risk]
```

Rules:
- Each packet has only one owner responsible for write scope
- Do not allow two lanes to edit the same file without a clear merge plan
- Reviewer lane must review from packet + evidence, not absorb the entire context implementer
- If the host does not have subagents, still use this packet to keep sequential passwords separate

## Checkpoint Artifact

Short Artifact should have:

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

If the task lasts more than one phase or has multiple checkpoints, persist the artifact with `scripts/track_execution_progress.py`.

For example:

```powershell
python scripts/track_execution_progress.py "Checkout retry ordering" `
  --mode checkpoint-batch `
  --stage implement-slice-1 `
  --lane implementer `
  --model-tier capable `
  --proof "failing retry reproduction" `
  --done "packet locked" `
  --next "rerun targeted queue scenario"
```

## Execution Packet

Before editing a medium/large slice, the minimum packet should have:

```text
Execution packet:
- Sources: [plan/spec/design/spec-review]
- Current slice: [...]
- File/surface scope: [...]
- Proof before progress: [...]
- Out of scope: [...]
- Reopen if: [...]
```

This packet is the bridge between `plan/architect/spec-review` and `build`.

## Stage Exit Criteria

A stage or slice should only be considered complete when:
- The proof of that slice has passed
- The relevant boundary has not been breached
- checkpoint clearly says next slice or blocker
- No more silent assumptions are pushed to the next stage

## Chain Visibility

When the task is no longer a single execution checkpoint but a long chain:

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

Persist equals `scripts/track_chain_status.py` when:
- chain goes through 3+ stages
- There are many skills involved
- need to pause/resume but still see the status immediately
- There are many lanes such as implement/review/gate that need to be looked at separately

For example:

```powershell
python scripts/track_chain_status.py "Checkout rewrite flow" `
  --project-name example-project `
  --current-stage spec-review `
  --active-skill build `
  --active-skill spec-review `
  --active-lane implementer `
  --active-lane spec-reviewer `
  --lane-model implementer=capable `
  --lane-model spec-reviewer=capable `
  --review-iteration 2 `
  --max-review-iterations 3 `
  --gate-decision conditional
```

## Bounded Review Loops

Spec-review and review lanes cannot be revised indefinitely.

Default rules:
- `spec-review` maximum `3` round `revise`
- exceed threshold -> `blocked` and return to `plan` or `architect`
- Each round of revision must indicate the correct part that needs fixing, without repeating vague feedback

This keeps execution from devolving into endless review theater.

## Completion States

|State | Meaning|
|-------|---------|
|`in-progress` | Not enough evidence to handoff|
|`ready-for-review` | Verified the implementation and waiting for the final review|
|`ready-for-merge` | Only use when the scope is small or the review is clear|
|`blocked-by-residual-risk` | The risk or blocker is still large, not considered done yet|

## Anti-Patterns

- Use `parallel-safe` when the boundary is unclear
- Start coding from "what's easiest" instead of from the execution packet
- Do not record checkpoints for large work and then summarize from memory at the end of the session
- Use `ready-for-merge` while there is still unverified risk
- Handoff only says "almost done" without a clear state
