---
name: dispatch-subagents
type: flexible
triggers:
  - host supports native subagents and the task has clear independent slices
  - host supports native subagents and reviewer lanes must stay independent
  - explicit request to delegate or split safe parallel work
quality_gates:
  - Delegation boundary explicit before spawn
  - Fresh packets per subagent
  - Non-overlapping ownership for write scopes
  - Review lane independence preserved
  - Merge and verification plan clearly before waiting
---

# Dispatch Subagents - Codex Multi-Agent Runtime

> Goal: map Forge lane policy to real Codex subagents without losing boundary control, evidence discipline, or review independence.

<HARD-GATE>
- Do not spawn subagents when boundaries are unclear or files will overlap materially.
- Do not fork full thread context by default. Build a fresh packet first.
- Do not dispatch parallel implementers into the same write scope.
- Do not wait on subagents while the controller has non-overlapping work to do.
- If the repo is dirty and the task is high-risk, reassess `worktree` before `subagent-split`.
</HARD-GATE>

## When To Use

Use this workflow when at least one is true:
- route/build selected `parallel-safe`
- route/build selected reviewer lanes and Codex can run them as independent subagents
- the user explicitly asks for delegation or parallel subagent work

Do not use this workflow when:
- root cause is still unclear
- one fix may collapse several failures together
- two slices need the same files or the same shared mutable state
- the controller cannot write a tight packet with proof and ownership

## Delegation Modes

|Mode | Use when | Subagent patterns|
|------|----------|------------------|
|`parallel-split` | Independent BUILD/DEBUG/OPTIMIZE slices with clear boundaries | 1 worker per slice, merged by controller|
|`independent-reviewer` | Forge pipeline requires spec/quality/deploy review lanes | 1 implementer worker + read-only reviewer lanes|
|`sequential-fallback` | Bundle wants independent lanes but safe parallelism is not justified | No spawn, keep lanes separate as controller passes|

## Role Mapping

|Forge lane | Codex roles | Notes|
|-----------|------------|-------|
|`implementer` | `worker` | Owns code changes in an explicit file scope|
|`spec-reviewer` | `default` | Read-only unless controller explicitly reassigns fixes|
|`quality-reviewer` | `default` | Findings first, patching only after ownership is reassigned|
|`navigator` | controller or `explorer` | Use `explorer` only for bounded read-only codebase questions|

Rules:
- `worker` must be told which files it owns
- reviewers should normally stay read-only
- `explorer` is for specific codebase questions, not broad implementation

## Package Contract

Every spawned subagent gets a self-contained packet:

```text
Delegation packets:
- Goal: [...]
- Current slice or review question: [...]
- Owned files / write scope: [...]
- Files to avoid: [...]
- Allowed reads / supporting artifacts: [...]
- Proof before progress: [...]
- Verification to rerun: [...]
- Return contract: [status, changed files, verification, residual risk]
```

Default stance:
- `fork_context=false`
- controller curates exactly the context needed
- include spec or diff excerpts directly if they are required

Use `fork_context=true` only when the subagent truly needs the exact same session state.

## Spawn Rules

### Parallel implementers

Use only when:
- each slice has a stable boundary
- each slice can verify independently
- expected write scopes do not overlap. expected write scopes do not overlap

Controller duties:
1. lock slice boundaries first
2. assign one worker per slice
3. keep ownership disjoint
4. integrate results and rerun shared verification

### Independent reviewers

Use when Forge chose `implementer-quality`, `implementer-spec-quality`, or `deploy-gate`.

Controller duties:
1. let implementer finish its slice and verification
2. send a review packet with spec, changed files, and evidence
3. collect findings before assigning any fix work
4. If fixes are needed, hand ownership back to the implementer worker or a new worker

## Status Contract

Subagents should return one of:
- `DONE`: slice complete, verification included
- `DONE_WITH_CONCERNS`: complete but with obvious doubt or residual risk
- `NEEDS_CONTEXT`: packet missing a concrete fact or artifact
- `BLOCKED`: cannot proceed safely within current ownership or context

Reviewer lanes should return:
- findings by severity
- explicit no-finding rationale when clean
- residual risk or testing gaps

## Controller Loop

```text
1. Choose delegation mode from Forge route/build policy
2. Write packets before spawning
3. Spawn implementers/reviewers with explicit ownership
4. Do non-overlapping controller work immediately
5. Integrate results
6. Rerun shared verification
7. Update chain status or checkpoint if the chain stays long
```

## Merge Discipline

- Do not merge subagent results blindly
- Check for file overlap before integration
- Run shared verification after integration, not just per-slice checks
- If reviewers disagree with implementer evidence, keep the issue open until re-review passes

## Codex Notes

- Prefer `spawn_agent` with small, well-scoped tasks
- Prefer `worker` for code edits and `default` for reviewer lanes
- Use `wait_agent` only when blocked on the result
- Reuse an agent only when the follow-up is tightly coupled to its prior packet

## Activation Announcement

```text
Forge: dispatch-subagents | fresh packet, explicit ownership, review stays independent
```
