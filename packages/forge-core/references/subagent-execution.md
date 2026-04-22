# Forge Subagent Execution

> Use this when a host can dispatch independent workers or reviewer lanes. The controller still owns Forge routing, execution packets, verification strategy, and final claims.

## Target

- use packet-first dispatch instead of raw task text
- keep subagents scoped to one role, one packet, and one write owner
- run spec-review-before-quality-review for every medium+ subagent slice
- enforce spec compliance before code quality so scope gaps are fixed before maintainability review
- preserve the same quality bar on hosts without subagents by running the lanes sequentially
- use abstract model/tier guidance instead of vendor model names
- end every lane with a concrete Return format, status, evidence, and residual risk
- hand a consolidated packet to the final reviewer before quality-gate claims
- use `subagent-prompts/final-reviewer-prompt.md` when the final review runs as a subagent lane

## Core Contract

Forge subagents are execution lanes, not a second orchestrator.

Rules:
- the controller prepares the Forge execution packet
- the controller assigns owned write scope and allowed reads before dispatch
- the subagent may ask for context, but may not expand scope silently
- each subagent must keep TDD discipline when changing behavior
- each subagent must answer with the Evidence response contract
- no two subagents edit the same file unless the controller has a merge plan
- reviewer lanes review from packet plus evidence, not from the full chat transcript

## Pipeline Selection

| Pipeline | Use when | Lane order |
|----------|----------|------------|
| `single-lane` | Small bounded work, no independent review needed | `implementer` |
| `implementer-quality` | Host has no subagents, or the work is sequential but still needs review | `implementer` -> `spec-reviewer` -> `quality-reviewer` |
| `implementer-subagent-quality` | Host has subagents and the work is medium+ with clear slice boundaries | `implementer-subagent(s)` -> `spec-reviewer` -> `quality-reviewer` -> `final-reviewer` |

Rules:
- prefer `implementer-subagent-quality` for medium+ work only when boundaries, ownership, and verification are explicit
- stay on `single-lane` for small tasks unless risk or blast radius justifies review
- use `implementer-quality` as the fallback for hosts without subagents
- do not split work that shares the same file ownership without a merge plan
- do not dispatch a subagent until the Forge execution packet is complete enough to run without guessing

## Packet-First Dispatch

Packet-first dispatch means every lane receives a Forge execution packet before any implementation or review instruction.

```text
Forge execution packet:
- Packet ID / parent packet: [...]
- Role: [implementer/spec-reviewer/quality-reviewer/final-reviewer]
- Slice goal: [...]
- Owned files / write scope: [...]
- Allowed reads / shared artifacts: [...]
- Source plan/spec/design: [...]
- Out of scope: [...]
- Dependencies: [...]
- Proof before progress: [...]
- TDD discipline: [failing test/repro first, or explicit no-harness reason]
- Verification to rerun before handoff: [...]
- Evidence response contract: [required]
- Return format: [status, summary, changed files, verification, residual risk]
```

If a field is unknown and material to correctness, dispatch should stop with `NEEDS_CONTEXT` rather than forcing the worker to infer the answer.

## Status Protocol

Every subagent response must begin with one of these statuses.

| Status | Meaning | Controller action |
|--------|---------|-------------------|
| `DONE` | Work is complete, verification ran, and no material concern remains | Proceed to spec review |
| `DONE_WITH_CONCERNS` | Work is complete enough to review, but concerns or residual risk remain | Read concerns, address correctness/scope issues, note observational concerns, then decide whether to review or redispatch |
| `NEEDS_CONTEXT` | The packet is missing context required for safe execution | Provide the missing context and redispatch with a revised packet |
| `BLOCKED` | The worker cannot make safe progress from the current packet or capability tier | Classify the blocker before continuing |

`BLOCKED` handling:
- context problem -> add context and redispatch
- reasoning/capability problem -> upgrade the lane tier or assign a stronger reviewer
- slice too large -> decompose into smaller packets
- plan/spec wrong -> return to `brainstorm` or `plan`, or escalate to the human controller
- repo/tool failure -> record command output and choose the next strongest evidence path

## Spec-Review-Before-Quality-Review

Order matters. Forge reviews the result in two different ways:

1. `spec-reviewer`: checks whether the implementation satisfies the Forge execution packet, source plan, stated scope, and user request.
2. `quality-reviewer`: checks maintainability, correctness risk, tests, error handling, integration fit, and evidence strength.

Rules:
- do not send a slice to `quality-reviewer` until the spec review is `DONE` or explicitly accepted with `DONE_WITH_CONCERNS`
- do not let quality review rewrite the spec; scope disagreement goes back to spec review or the controller
- if spec review finds missing requirements, redispatch the implementer before quality review
- if quality review finds implementation risk, return to the implementer with the specific finding and required evidence

## Model/Tier Guidance

Forge uses high-level tiers instead of vendor-specific model names.

| Lane | Default tier | Upgrade when |
|------|--------------|--------------|
| `implementer` | `standard` | large slice, migration, auth, payment, cross-package behavior, or repeated failures |
| `spec-reviewer` | `standard` | ambiguous requirements, high blast radius, or user-facing contract changes |
| `quality-reviewer` | `standard` | release-critical, regression recovery, security-sensitive, or integration-heavy work |
| `final-reviewer` | `capable` for large work, otherwise `standard` | many slices, broad diff, or conflicting reviewer signals |

Keep cheap tiers for navigation and artifact reading. Do not force every lane to the strongest tier when the packet is bounded and evidence is clear.

## Fallback For Hosts Without Subagents

Hosts without subagents must still preserve lane separation.

Sequential fallback:
1. controller prepares the same Forge execution packet
2. implementer pass runs and returns the status protocol
3. controller starts a fresh spec-reviewer pass from packet, diff, and evidence
4. controller starts a fresh quality-reviewer pass only after spec review
5. controller performs final reviewer handoff as a holistic self-review when no reviewer subagent exists

The fallback may run in one conversation, but it must not collapse implementation, spec review, and quality review into a single stream of thought.

## Final Reviewer Handoff

After all slices are complete, the controller prepares a final reviewer handoff packet before quality-gate claims.

```text
Final reviewer handoff:
- Source request and accepted plan/spec: [...]
- Execution packet history: [...]
- Changed files and ownership map: [...]
- Implementer statuses: [...]
- Spec-reviewer dispositions: [...]
- Quality-reviewer dispositions: [...]
- Verification evidence: [...]
- Known residual risks: [...]
- Open concerns requiring human decision: [...]
- Return format: [findings, disposition, required fixes, gate recommendation]
```

Rules:
- final review is holistic; it checks whether the combined result still matches the original intent
- medium work should prefer final review when the diff spans multiple files or packets
- large work should require final review before quality-gate
- if no subagent exists, the controller runs the same checklist as a self-review and clearly states that it is not independent

## Return Format

Each subagent must return this shape:

```text
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Packet ID: [...]
Role: [...]
Summary: [...]
Changed files: [...]
Verification: [...]
Evidence response contract:
- I verified: [fresh evidence]. Correct because [reason]. Fixed: [change].
- I evaluated: [evidence]. The current code stays because [reason].
- Clarification needed: [single precise question].
Concerns: [...]
Residual risk: [...]
Next handoff: [spec-reviewer/quality-reviewer/final-reviewer/controller]
```

Use only the lines that apply, but keep the status, packet ID, verification, concerns, and residual risk explicit.
