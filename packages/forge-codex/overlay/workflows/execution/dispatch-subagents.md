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
  - Merge and verification plan clear before waiting
---

# Dispatch Subagents - Codex Multi-Agent Runtime

> Goal: map Forge lane policy to real Codex subagents without losing boundary control, evidence discipline, or review independence.

<HARD-GATE>
- Do not spawn subagents when boundaries are unclear or write scopes overlap materially.
- Do not fork the full thread by default. Build a fresh packet first.
- Do not send parallel implementers into the same write scope.
- Do not wait on subagents while the controller still has non-overlapping work to do.
- If the repo is dirty and the task has a broad or multi-slice blast radius, reconsider `worktree` before `subagent-split`.
</HARD-GATE>

## When To Use

Use this workflow when at least one of these is true:
- route/build selected `parallel-safe`
- route/build selected reviewer lanes and Codex can run them as independent subagents
- the user explicitly asked for delegation or parallel subagent work

Do not use this workflow when:
- root cause is still unclear
- one fix may collapse several failures into the same slice
- two slices need the same files or the same mutable shared state
- the controller cannot write a tight packet with proof and ownership

## Delegation Modes

|Mode | Use when | Subagent pattern|
|------|----------|-----------------|
|`parallel-split` | Independent BUILD/DEBUG/OPTIMIZE slices with clear boundaries | 1 worker per slice, merged by the controller|
|`independent-reviewer` | Forge requires quality/deploy review lanes | 1 implementer worker + read-only reviewer lanes|
|`sequential-fallback` | Distinct lanes are needed but safe parallelism is not justified | No spawn; keep the lanes separate as controller-managed passes|

## Role Mapping

|Forge lane | Codex role | Notes|
|-----------|------------|------|
|`implementer` | `worker` | Owns code changes within an explicit file scope|
|`quality-reviewer` | `default` | Findings first; patch only after ownership is reassigned|
|`navigator` | controller or `explorer` | Use `explorer` only for bounded read-only codebase questions|

Rules:
- every `worker` must be told exactly which files it owns
- reviewers should normally remain read-only
- `explorer` is for targeted codebase questions, not broad implementation work

## Packet Contract

Every spawned subagent gets a self-contained packet:

```text
Delegation packet:
- Packet ID / parent packet: [...]
- Goal: [...]
- Current slice or review question: [...]
- Depends on packets: [...]
- Owned files / write scope: [...]
- Files to avoid: [...]
- Allowed reads / supporting artifacts: [...]
- Proof before progress: [...]
- Verification to rerun: [...]
- Browser QA classification / scope / status: [...]
- Return contract: [status, changed files, verification, residual risk]
```

Default stance:
- `fork_context=false`
- the controller curates only the context the subagent actually needs
- include spec or diff excerpts directly when they matter

Use `fork_context=true` only when the subagent genuinely needs the same full session state.

## Spawn Rules

### Parallel Implementers

Use only when:
- each slice has a stable boundary
- each slice can verify independently
- expected write scopes do not overlap

Controller duties:
1. lock slice boundaries first
2. assign one worker per slice
3. keep ownership disjoint
4. integrate results and rerun shared verification

### Independent Reviewers

Use when Forge selected `implementer-quality` or `deploy-gate`.

Controller duties:
1. let the implementer finish its slice and verification
2. send a review packet with the spec, changed files, and evidence
3. collect findings before assigning any fix work
4. if fixes are needed, hand ownership back to the implementer or a new worker

## Status Contract

Subagents should return one of:
- `DONE`: slice complete, verification included
- `DONE_WITH_CONCERNS`: complete, but with residual risk or obvious doubt
- `NEEDS_CONTEXT`: the packet is missing a concrete fact or artifact
- `BLOCKED`: cannot proceed safely within the current scope or ownership

Reviewer lanes should return:
- findings by severity
- explicit no-finding rationale when clean
- residual risk or testing gaps

## Controller Loop

```text
1. Choose the delegation mode from Forge route/build policy
2. Write packets before spawning
3. Spawn implementers/reviewers with explicit ownership
4. Do non-overlapping controller work immediately
5. Integrate results
6. Rerun shared verification
7. Update chain status or checkpoint if the chain remains long
```

## Merge Discipline

- Do not merge subagent results blindly
- Check for file overlap before integration
- Run shared verification after integration, not just per-slice checks
- If reviewers disagree with implementer evidence, keep the issue open until re-review passes

## Codex Notes

- Prefer `spawn_agent` with small, well-scoped tasks
- Prefer `worker` for code edits and `default` for reviewer lanes
- Use `wait_agent` only when you are actually blocked on the result
- Reuse an agent only when the follow-up is tightly coupled to its prior packet

## Activation Announcement

```text
Forge: dispatch-subagents | fresh packet, explicit ownership, review stays independent
```
