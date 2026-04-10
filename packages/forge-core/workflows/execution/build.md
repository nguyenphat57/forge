---
name: build
type: rigid
triggers:
  - intent: BUILD
  - shortcut: /code
  - explicit quick hint for small, clear, low-risk work
quality_gates:
  - Verification strategy defined before editing
  - Execution mode selected for medium/large work
  - Execution pipeline explicit for medium/large or high-risk work
  - Execution packet explicit for medium/large work
  - Isolation recommendation explicit for high-risk work
  - Spec-review completed when required
  - Relevant checks pass
  - Reviewer-style pass completed for medium/large
  - Completion state explicit before handover
---

# Build - Code Implementation

## The Iron Law

```
NO BEHAVIORAL CHANGE WITHOUT DEFINING VERIFICATION FIRST
```

<HARD-GATE>
- Before any behavior-changing edit, run a process precheck: repo state, plan/spec/change artifact, and the baseline verification path.
- Small creative work still needs an approved quick plan/design packet before build.
- Medium/large tasks: must have impact analysis before editing.
- Large tasks: must select execution mode before batch coding.
- Medium/large or high-risk work: must close the execution pipeline before expanding.
- Medium+ work in a dirty repo should default toward `worktree` and a clean baseline before modifying.
- High-risk or dirty-repo work: isolation stance must be locked (`same tree`, `worktree`, or host-supported subagent split`) before modifying.
- Large/high-risk implementation: if `spec-review` applicable, build only starts when readiness is `go`.
- Behavioral changes: prioritize failing test or reproduce before editing.
- If there is no viable harness, you must clearly state why and use the strongest remaining verification method.
- Do not claim "done" without new evidence.
</HARD-GATE>

---

## Process Flow

```mermaid
flowchart TD
    A[Receive task] --> B[Classify task]
    B --> C[Impact analysis if needed]
    C --> D[Choose execution mode if needed]
    D --> E[Choose execution pipeline + lane stance]
    E --> F[Take execution packet]
    F --> G[Choose verification strategy]
    G --> H{Behavior change + harness available?}
    H -->|Yes| I[Write failing test/reproduction]
    H -->|No| J[Lock fallback command/check]
    I --> K[Act on one slice]
    J --> K
    K --> L[Run slice proof + boundary checks]
    L --> M[Reflect: drift / next slice / reopen?]
    M --> N{Pass + still on-plan?}
    N -->|No| O[Fix from evidence or go back to plan/debug]
    O --> F
    N -->|Yes| P[Update checkpoint if the task is long-running]
    P --> Q[Reviewer lane / reviewer-style pass]
    Q --> R[Set completion state]
    R --> S[Handover]
```

## Task Classes

|Task type | How to verify before editing|
|-----------|---------------------------|
|Feature / bugfix has test harness | Failing test or reproduction|
|Feature / bugfix without harness | Manual reproduction is clear, failing command, or smoke path|
|Config / build script / release chore | Build, lint, typecheck, diff, or target command|
|Docs only | Link / path / content check, do not pretend to have a test|

## Impact Analysis (required for medium/large)

Answer before coding:
1. Which files are affected?
2. Which callers/consumers must update?
3. Which edge cases are fragile?
4. What verification needs to be added or edited?
5. If the scope is >3 files or there is a large assumption -> notify the user before editing

## Execution Packet Intake

Before editing `medium/large`, the build must close the slice under construction:

```text
Execution packet:
- Packet ID: [...]
- Packet mode: [standard / fast-lane]
- Parent packet: [...]
- Sources: [plan/spec/design/spec-review]
- Goal: [...]
- Current slice: [...]
- Baseline: [...]
- Exact files / path scope: [...]
- Owned files / write scope: [...]
- Depends on packets: [...]
- Unblocks packets: [...]
- Merge target / strategy: [...]
- Overlap risk / write-scope conflicts: [...]
- Review readiness / merge readiness / completion gate: [...]
- Verification to rerun: [...]
- Browser QA classification: [not-needed / optional-accelerator / required-for-this-packet]
- Proof before progress: [...]
- Out of scope for this slice: [...]
- Reopen if: [...]
```

Rules:
- Do not edit until `current slice` is finalized
- Do not edit until the baseline command or check is named.
- Don't combine multiple slices into one edit just because it's "convenient".
- If you need to touch a file/boundary outside the packet to save the design, stop and reopen `plan`, `architect`, or `spec-review`
- `track_execution_progress.py` is the canonical packet record for medium/large build work; summaries and dispatch wrappers should read from that packet instead of inventing a second schema

## Fast Lane Contract V1

Fast lane is a light packet mode for truly small low-risk slices, not a second execution system.

Eligibility:

- low blast radius
- narrow owned write scope
- no packet graph dependency or merge choreography needed
- no schema/auth/payment/public-interface/release-tail boundary

Required fast lane fields:

- `packet_id`, `packet_mode`, `label`, `goal`, `status`
- `exact_files_or_paths_in_scope`, `owned_files_or_write_scope`
- `baseline_or_clean_start_proof`, `proof_before_progress`, `verification_to_rerun`
- `residual_risk`, `next_steps`

Rules:

- fast lane cannot skip baseline proof, verification rerun, or residual-risk capture
- fast lane state still persists through `track_execution_progress.py`
- if dependency/overlap risk appears, escalate to standard packet mode instead of patching around missing graph fields

## Execution Mode Selection

Choose mode before coding medium/large to avoid changing tactics at the same time:

|Mode | Use when | Avoid when|
|------|----------|-----------|
|`single-track` | A major critical path, coupled change, needs to keep the context tight | There are many truly independent workstreams|
|`checkpoint-batch` | Large tasks have many sequential steps, need to clearly divide checkpoints The task is too small or too coupled to split the batch|
|`parallel-safe` | There are many independent slices, the interface/boundary is clear The contract has not been finalized or the blast radius overlaps|

Rule:
- `small` -> almost always `single-track`
- `medium` -> default `single-track`, only raised to `checkpoint-batch` when there are 2+ clear intersections
- `large` -> forced to select a mode
- If in doubt whether it is safe to parallelize or not, return to `single-track`
- If the repo is dirty or the slice is behavior-changing, favor `worktree` and a clean baseline before modifying.

If the task is long, log the checkpoint artifact with script `scripts/track_execution_progress.py`.
To see the mode chooser and complete states more concisely, read `references/execution-delivery.md`.

## Execution Pipeline Selection

Pipeline is Forge's way of separating implementation/spec/quality lanes to avoid both code and self-validation.

|Pipelines | Use when | Lanes|
|----------|----------|-------|
|`single-lane` | Small or medium low-risk | `implementer`|
|`implementer-quality` | Medium/large with clear enough specs but still needs independent lane review | `implementer` -> `quality-reviewer`|
|`implementer-spec-quality` | `spec-review` applicable or build high-risk | `implementer` -> `spec-reviewer` -> `quality-reviewer`|

Rules:
- `BUILD` has `spec-review` -> defaults to `implementer-spec-quality`
- `large` or stronger profile `standard` -> must have at least `quality-reviewer`
- Host has subagents -> lane can run independently
- Host does not have subagents -> still has to run sequentially in lanes, not combining thoughts into a single pass
- `implementer-spec-quality` must run `spec-compliance` before `quality-pass`
- If `spec-compliance` finds drift, return to implementer and do not advance to `quality-reviewer`
- Reviewer lanes must close the slice explicitly before the implementer moves on.

## Lane Model Stance

Forge uses an abstract tier instead of a hard-coded vendor model:

|Lane | Default tier|
|------|--------------|
|`navigator` | `cheap`|
|`implementer` | `standard`|
|`spec-reviewer` | `capable`|
|`quality-reviewer` | `standard`|

Rules:
- `large` -> implement/review tilted lanes `capable`
- `release-critical`, `migration-critical`, `external-interface`, `regression-recovery` -> related review lane must go to `capable`
- If the task is just a bounded low-risk slice, keeping the cheaper lane is the right choice
- Medium+ slices with behavior changes should favor the stronger review lane when the baseline is not trivial.

## Isolation Recommendation

For multi-step `large` or `high-risk` work, lock the isolation stance before starting:

|Stance | Use when|
|--------|----------|
|`same-tree` | Small enough task or clean repo, low blast radius|
|`worktree` | The repo is dirty, the task is high risk, or the change set needs to be isolated|
|`subagent-split` | Host supports subagents and tasks with many clear boundary slices|

Rule:
- If the repo is dirty and the task is not small -> prioritize `worktree`
- If the task is medium+ and behavior-changing, prefer `worktree` unless the scope is already isolated and the baseline is clean.
- If the boundary is unclear -> do not use `subagent-split`
- If `subagent-split` is selected, there must be a clear enough chain status or checkpoint to merge the results

When `worktree` is selected, bootstrap it explicitly:

```powershell
python scripts/prepare_worktree.py --workspace <workspace> --name <slice> --baseline-command "<baseline>"
```

The packet should keep:
- worktree path
- ignore-safety proof for project-local worktree roots
- baseline result from that isolated tree

## Subagent Split Packet

When building actually uses `subagent-split`, each subagent must receive packets on its own instead of just saying "go read the code and do it":

```text
Delegation packets:
- Packet ID / parent packet: [...]
- Slice goal: [...]
- Owned files / write scope: [...]
- Depends on packets: [...]
- Shared reads allowed: [...]
- Proof before progress: [...]
- Verification to rerun before handoff: [...]
- Browser QA classification/scope/status: [...]
- Return with: [status, changed files, verification, residual risk]
```

Rules:
- Use a fresh worker for each slice or review lane. Do not reuse stale context after the packet changes materially.
- Do not assign overlapping write scopes between two subagents
- If the repo is dirty or the blast radius is high, consider `worktree` before `subagent-split`
- If the packet does not clearly state proof or ownership, return `plan` / `spec-review` instead of blind dispatch

## Spec-Review Dependency

`Spec-review` is the gate before build when:
- task `large`
- task `medium` but has contract/schema/migration/auth/payment/public interface/high-risk boundary

Build should not be considered "as if the spec is sufficient" if:
- The plan also states open assumption
- The architect just changed the system shape to a large extent
- verification strategy is missing for important boundaries

## Verification Strategy

### If there is a harness
- Write failing test for behavior that needs to be changed
- Verify test fails for correct reason
- Minimum implementation
- Rerun related tests and necessary checks

### Without harness
- Clearly state the reason why the test cannot be used
- Create specific reproduction/check before editing
- After editing, run the correct reproduction/check again

### Verification ladder
- `Slice proof`: smallest check that proves the current slice is correct
- `Boundary check`: added when slice touches contract, schema, integration, auth, migration, or external interface
- `Broader suite`: added when blast radius is wide, release-critical, or just has regression

Rule:
- Don't jump straight into the big suite to cover up the lack of slice proof
- Do not stop at slice proof when the boundary has just been clearly changed

### Fast-Fail Order
- 1. Packet + proof-before-progress locked
- 2. Failing test or reproduction captured
- 3. Slice proof pass
- 4. Boundary check pass if there is contract/schema/integration blast radius
- 5. Reviewer lane or reviewer-style pass
- 6. Quality gate / completion claim

Do not use large suites or the phrase "built pass" to skip steps 1-3.

### Absolutely do not do it
- Say "this task is too small to test"
- Reported test-first when in reality there was no test
- After editing, then think about how to verify

## Anti-Rationalization

|Defense | Truth|
|----------|---------|
|"Need to explore first before writing test/repro" | Explore may be needed, but the verification strategy for behavior change must still be finalized before editing|
|"TDD is not practical in this repo" | If the harness can be used, there must be a specific technical reason for removing RED, not a feeling|
|"Keeping the old code for reference should fix it temporarily" | Reference is not a substitute for reproduction/test; must know exactly which behavior is changing|
|"It's difficult to test so skip quickly" | When testing is difficult, switch to a stronger reproduction/check instead of giving up verification|
|"Fix it, then add more tests later" | Test-after easily validates the written code, but cannot prove the original intent|
|"Plan clearly, just code at once" | Large work still needs execution mode and checkpoint to avoid drifting or missing handoff state|

Code examples:

Bad:

```text
"I'll patch it first to move faster, then think about how to test it."
```

Good:

```text
"Verification before editing: reproduce with [command/scenario]. Then change the code and rerun that exact check."
```

## Reason -> Act -> Verify -> Reflect

For all non-small slices:

1. `Reason` -> read current packet, repeat proof and boundary
2. `Act` -> fix the smallest part enough to move forward
3. `Verify` -> runs the correct proof/check for the slice
4. `Reflect` -> recorded drift, next slice, blocker, or signal must reopen upstream

Rules:
- Do not accumulate many unverified changes before testing them once
- If verification fails for unexpected reasons, the first response is to re-read the packet and do impact analysis
- `Reflect` must decide clearly: continue with the next slice, edit the current slice, or go upstream

---

## Two-Stage Review

### Stage 1: Spec Compliance
- Correct scope the user requested?
- Are there any unstated assumptions?
- Are there excess features or missing requirements?

### Stage 2: Code Quality
- Is the naming and structure easy to read?
- Error handling / validation enough?
- Consumers / imports / types still valid?
- Verification is enough for blast radius?

If the execution pipeline has `quality-reviewer`, this pass must be read as a separate lane, not just looking at the code itself in the same execution rhythm.
If the execution pipeline has `spec-reviewer`, it runs first as the `spec-compliance` lane and must close cleanly before `quality-reviewer` starts.
If the host supports subagents, the reviewer lane should receive a shortened controller packet: scope, evidence, changed files/diff, and the specific review question. Do not force the reviewer to reconstruct intent from the full session.

## Drift / Reopen Rules

Build must stop and turn upstream when:
- The current slice needs to physically add a boundary or file outside the packet
- plan/spec-design just revealed the wrong assumption
- verify failure repeats 3 rounds without clear root cause
- completes a slice but the next slice changes the chosen direction

Suggested routes:
- drift to shape / scope / sequencing -> return to `plan`
- drift about contract / schema / architecture -> return to `architect` or `spec-review`
- drift towards incomprehensible behavior -> to `debug`

## Completion States

Before handover, the build must clearly assign a state:

|State | What does it mean?|
|-------|-------------|
|`in-progress` | Not enough evidence to handoff|
|`ready-for-review` | Verified my work and waiting for final review/inspection|
|`ready-for-merge` | Only use when scope is small, verification is strong, and there are no known finding/blockers|
|`blocked-by-residual-risk` | There is a large enough risk/blocker so it is not considered done|

Do not use vague sentences like "almost done", "basically okay", "probably can be merged".

## Verification Checklist

- [ ] Verification strategy has been finalized before editing
- [ ] Task medium/large already has impact analysis
- [ ] Task medium/large has selected the appropriate execution mode
- [ ] High-risk work has clear isolation recommendation
- [ ] Task medium/large already has an execution packet for the current slice
- [ ] If applicable, spec-review returned `go`
- [ ] Behavioral change had a failing test/reproduction or the reason for not having a harness
- [ ] Slice proof has been run before proceeding to the next slice
- [ ] Long task has updated checkpoint or clearly stated why it is not needed
- [ ] Related checks have been rerun after correction
- [ ] Read output, don't just run the command for the sake of it
- [ ] Reviewer-style pass is final
- [ ] Completion state is explicit
- [ ] Clearly noted the part that cannot be verified (if any)

## Language / Runtime Integration

```
- Respect the repo's existing toolchain and package/build system
- Keep contracts/interfaces explicit according to the capabilities of the language and framework in use
- Validate input at the boundary, whether the repo is dynamic or strongly typed
- If you change a contract, update callers/adapters at the same time
- If the repo clearly maps to Python/Java/Go/.NET and a suitable companion skill exists, load that companion for idiom/framework detail
- If no companion skill exists, continue with the existing Forge workflows. Do not stop just because a runtime-specific layer is missing.
- Forge still owns verification strategy, evidence gates, and residual-risk reporting
```

## Handover

```
Build report:
- Scope: [...]
- Execution mode: [single-track/checkpoint-batch/parallel-safe]
- Execution pipeline: [single-lane/implementer-quality/implementer-spec-quality]
- Isolation stance: [same-tree/worktree/subagent-split]
- Lane model stance: [implementer=standard, spec-reviewer=capable, quality-reviewer=standard]
- Spec-review: [go/n-a]
- Current/last slice: [...]
- Progress checkpoint: [artifact path or n/a]
- Files changed: [...]
- Verified: [command/check] -> [result]
- Evidence response: [I verified:... / I investigated:... / Clarification needed:...]
- Completion state: [ready-for-review/ready-for-merge/blocked-by-residual-risk]
- Unverified: [...]
- Residual risk: [...]
```

## Activation Announcement

```
Forge: build | verification-first, impact analysis before editing
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: build`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.