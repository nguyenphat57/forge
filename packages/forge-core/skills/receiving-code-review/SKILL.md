---
name: forge-receiving-code-review
description: Use when the user, reviewer, CI, or another agent gives code review feedback or requested changes.
---

# Forge Receiving Code Review

<EXTREMELY-IMPORTANT>
Do not blindly agree with review feedback. Investigate, decide, verify, and respond with evidence.

Technical correctness over social comfort. Actions and proof matter more than performative agreement.
</EXTREMELY-IMPORTANT>

## Core Principle

Review feedback is input to evaluate, not an order to obey blindly. Correct feedback should be fixed with proof. Incorrect or out-of-scope feedback should be challenged with evidence. Unclear feedback should be clarified before implementation.

## Use When

- The user pastes review feedback.
- A reviewer or CI requests changes.
- Feedback is unclear, technically questionable, stylistic, or conflicting.
- You need to address PR comments or review findings.

## Do Not Use When

- You are initiating a review; use `forge-requesting-code-review`.
- The issue is a failing test without review context; use `forge-systematic-debugging`.

## Response Pattern

```text
READ -> UNDERSTAND -> VERIFY -> EVALUATE -> RESPOND -> IMPLEMENT
```

1. Read all feedback before reacting.
2. Restate the actionable requirement in technical terms.
3. Verify against code, tests, docs, artifacts, or product constraints.
4. Decide whether the feedback is correct for this codebase and this request.
5. Respond with fix, reasoned pushback, or one precise clarification question.
6. Implement one item at a time and verify each material change.

Do not start editing from partial understanding when feedback items may interact.

## Forbidden Responses

Avoid performative agreement:

- "You're absolutely right."
- "Great point."
- "Excellent feedback."
- "Good catch" without proof or action.
- "I'll just implement that" before verification.

Use technical responses instead:

- "I verified this against <evidence>; the issue is valid. Fixing <specific change>."
- "I checked <evidence>; keeping current behavior because <reason>."
- "Clarification needed: <one precise question>."

## Feedback Matrix

| Feedback type | Response |
| --- | --- |
| Technically correct | Edit, verify, and report fresh evidence. |
| Unclear intent | Ask one precise question. |
| Technically questionable | Investigate first, then challenge with evidence if needed. |
| Stylistic preference | State convention, tradeoff, and decision. |
| Out of scope | Name the accepted scope and ask whether to expand. |
| Conflicting feedback | Stop, summarize conflict, and ask for the deciding priority. |
| YAGNI expansion | Check actual usage before adding unneeded surface. |

## Process

1. Restate the actionable feedback.
2. Inspect the code, tests, and relevant artifacts.
3. Decide: fix, keep, clarify, or split.
4. If fixing behavior, use `forge-test-driven-development` when a harness is viable.
5. Verify with the strongest relevant check.
6. Reply with evidence and disposition.

## Clarify Before Partial Implementation

For multi-item feedback:

1. Identify which items are clear and which are unclear.
2. If unclear items may affect the clear ones, ask before editing.
3. If clear items are independent, implement only those and explicitly defer the unclear ones.
4. Do not pretend a vague item is understood to keep momentum.

## External Feedback Skepticism

For external reviewers, CI suggestions, or agent feedback, check:

- Is the suggestion technically correct for this codebase?
- Does it break existing behavior, compatibility, or user intent?
- Is the current implementation intentional because of a constraint?
- Does the reviewer have the full context?
- Is this a requested requirement or an unneeded expansion?

If the feedback conflicts with the user's prior direction, stop and ask the user before changing direction.

## YAGNI Check

When a review suggests a "proper" feature, abstraction, endpoint, setting, export, or generalized design:

1. Search for actual usage.
2. Check whether the accepted plan requested it.
3. If unused and unrequested, ask whether to remove or defer it instead of building more surface.
4. If used or required, implement it with normal verification.

Do not add product surface just because a reviewer described a professional-looking solution.

## Implementation Order

For multiple valid findings:

1. Blocking correctness, security, data loss, build, or regression issues.
2. Simple mechanical fixes.
3. Behavior changes with TDD or a deterministic repro.
4. Refactors and maintainability changes.
5. Minor polish.

Verify material changes as you go. Do not batch unrelated review fixes and then guess which one caused a new failure.

## When To Push Back

Push back when:

- the suggestion is technically wrong
- it breaks a documented contract
- it violates YAGNI or accepted scope
- it conflicts with compatibility constraints
- it contradicts fresh verification
- it needs a product or architecture decision

Good pushback is short and evidence-based:

```text
I checked <evidence>. I do not think this change is correct because <technical reason>. The current behavior should stay unless we choose <tradeoff>.
```

## Response Shapes

- `I verified: [fresh evidence]. Correct because [reason]. Fixed: [change].`
- `I evaluated: [evidence]. The current code stays because [reason].`
- `Clarification needed: [single precise question].`
- `Deferred: [finding]. Reason: [scope/risk/dependency]. Needed decision: [question].`

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "Good catch, fixed." | Missing evidence and reason. |
| "Reviewer must be right." | Review feedback still needs technical validation. |
| "Style comments do not need verification." | They still need a clear decision. |
| "I'll fix the clear items and ask later." | Partial implementation can be wrong if unclear items interact. |
| "This looks more professional." | YAGNI still applies. |
| "Pushing back is impolite." | Evidence-based disagreement protects the codebase. |
| "Batch all review fixes together." | One bad change becomes harder to isolate. |

## GitHub And Threaded Reviews

When replying to threaded review comments, keep replies attached to the specific thread when the host supports it. Do not bury inline feedback in a general summary if the reviewer expects per-thread disposition.

## Integration

- Called by: `forge-requesting-code-review`, human reviewers, CI review surfaces, and external feedback in the thread.
- Calls next: `forge-test-driven-development`, `forge-systematic-debugging`, or `forge-verification-before-completion` depending on whether the feedback changes behavior, exposes a defect, or closes a claim.
- Pairs with: `forge-executing-plans` for the actual change slice and `forge-session-management` for review handoff continuity.
