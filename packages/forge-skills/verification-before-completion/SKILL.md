---
name: forge-verification-before-completion
description: Use when you are about to say done, fixed, ready, tests pass, mergeable, deployable, or complete.
---

# Forge Verification Before Completion

<EXTREMELY-IMPORTANT>
Use this before any completion, ready, fixed, passing, merge, PR, release, or deploy claim.

```text
NO CLAIMS WITHOUT FRESH EVIDENCE
```

If you have not run or inspected verification in this response window, you cannot claim it passes.
</EXTREMELY-IMPORTANT>

## Core Principle

Evidence before assertions, always.

Completion language without fresh proof is not efficiency; it is a false state report. This skill is the final claim boundary for Forge.

## Use When

- You are about to say done, fixed, ready, complete, tests pass, can merge, can ship, or can deploy.
- You are closing review feedback.
- You are handing off a branch or release-facing change.
- You are about to commit, create a PR, mark a task complete, or move to the next task.
- A worker, agent, CI summary, or previous run says the work succeeded.
- You want to express satisfaction such as "looks good", "all set", or "ready".

## Do Not Use When

- You are asking a single clarification and making no claim.
- You are reporting blocked status without implying completion.

## Gate Function

Before any success or completion claim:

1. Identify the exact claim.
2. Identify the command, artifact, diff, repro, or checklist that proves that claim.
3. Run or inspect the full proof fresh.
4. Read the output, exit code, failure count, and relevant warnings.
5. Compare the output to the claim.
6. If proof confirms it, state the claim with evidence.
7. If proof does not confirm it, state the actual status and blocker.

Skipping any step means the claim is not allowed.

## Required Checks

1. Name the claim target.
2. Name the verification method used before editing.
3. Rerun the same or stronger verification after the change.
4. Read the output.
5. Check blockers, conflicts, review findings, and residual risk.
6. For medium or risky work, confirm workflow-state or durable artifacts exist.
7. If merge, PR, or release-facing, confirm branch resolution is explicit.

## Continuity Closeout Gate

Before the final completion response, use `session_context.py closeout` when durable context exists: pending work, verification, risk, blocker, decision, or learning.

## Claim To Evidence Map

| Claim | Requires | Not sufficient |
| --- | --- | --- |
| `tests pass` | full relevant test command output with passing result | previous run, "should pass", partial test if claiming all |
| `lint clean` | linter command output with zero relevant errors | tests passing |
| `build succeeds` | build command exit success and relevant output | lint passing |
| `fixed` | original repro or failing test now passes | code changed, reviewer agreed |
| `regression test works` | RED -> GREEN proof, or explicit no-harness reason | test passes once without proving it caught the bug |
| `ready for review` | diff/artifact exists, verification run, known risks named | implementation summary only |
| `ready to merge` | review disposition, blockers/conflicts checked, verification fresh | local tests only |
| `docs updated` | path/content/diff verification | "changed the docs" |
| `agent completed` | controller inspected returned diff/evidence | agent status alone |
| `requirements met` | requirement checklist against accepted plan/spec | tests passing alone |

## Evidence Rules

- Fresh evidence beats prior memory.
- "Previously passed" is not evidence.
- Do not swap to a weaker check at the end.
- If verification cannot run, say `not verified`, name the blocker, and do not claim completion.
- Docs-only changes still need path, content, or diff verification.
- Agent reports are claims, not proof; inspect the diff or artifacts yourself.
- Partial verification can support a conditional status, not an unconditional completion claim.
- If a check fails and you believe it is unrelated, prove or state the residual risk explicitly.

## Evidence Packet

Report completion with this shape:

```text
Claim:
- <done/fixed/tests pass/ready/etc.>

Evidence:
- <command, artifact, diff, repro, checklist>
- <latest result>

Scope:
- <what the proof covers>

Residual risk:
- <what was not verified, or none known>

Decision:
- go | conditional | blocked
```

Use the packet mentally even when the final user response is shorter.

## RED-GREEN Claims

For harness-capable behavior changes:

- A regression or feature test must fail for the correct reason before implementation.
- After the fix, the same test must pass.
- If code was written before RED, delete it and restart from RED.
- If no harness is viable, name the no-harness reason and use the strongest available repro or smoke proof.

Do not claim a regression test is meaningful unless it proved the bug or missing behavior before the fix.

## Requirements Checklist

When claiming plan/spec completion:

1. Re-read the accepted request, spec, or plan.
2. Create a short checklist of required outcomes.
3. Mark each item as covered, changed, deferred, or blocked.
4. Verify the implementation and docs against that checklist.
5. Report any gap instead of compressing it into "done."

Tests passing does not prove all requirements were implemented.

## Decisions

- `go`: evidence is fresh and no blocker remains.
- `conditional`: evidence is partial and residual risk is explicit.
- `blocked`: evidence is missing or blocker is material.

## Not Verified Language

Use direct language when proof is missing:

```text
Not verified. I could not run <check> because <blocker>. Current evidence only shows <partial proof>. I am not claiming <claim>.
```

Do not soften missing proof with "should", "probably", "likely", "seems", or "looks good."

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "Small change, no need to rerun." | Completion claims require fresh evidence. |
| "CI passed earlier." | Earlier CI is stale unless it covers the final diff. |
| "Looks fixed." | Looks are not proof. |
| "Test failed but unrelated." | Prove or report residual risk. |
| "The agent said it passed." | Agent output is not controller verification. |
| "I only changed docs." | Docs still need path/content/diff proof. |
| "Different wording avoids the rule." | Any implication of success needs proof. |
| "I am tired and this is close enough." | Fatigue does not lower the evidence bar. |
| "Partial check is enough." | Partial check supports only a scoped or conditional claim. |

## Examples

Allowed:

```text
Verified with `python -m pytest packages/forge-core/tests/test_contracts.py -q`: 15 passed. Residual risk: full release suite not rerun.
```

Not allowed:

```text
Should be fixed now.
```

Allowed:

```text
Not verified. I could not run the browser smoke because the app server is unavailable. I only verified the diff content.
```

Not allowed:

```text
Looks good from the diff.
```

## Integration

- Called by: `forge-executing-plans`, `forge-receiving-code-review`, `forge-requesting-code-review`, and any release-facing closeout path.
- Calls next: `forge-finishing-a-development-branch` when the work is truly ready for merge, PR, keep, or discard decisions.
- Pairs with: `forge-session-management` for durable proof artifacts and `forge-systematic-debugging` when verification fails unexpectedly.
