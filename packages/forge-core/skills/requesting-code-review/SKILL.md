---
name: forge-requesting-code-review
description: Use when work is complete enough to review before merge, PR, handoff, or a ready claim.
---

# Forge Requesting Code Review

<EXTREMELY-IMPORTANT>
Use this before claiming work is ready, mergeable, or review-complete.

Findings first. Summary second.

Review early enough to catch defects before they compound, and late enough that the reviewer has a concrete diff, artifact, or evidence packet to inspect.
</EXTREMELY-IMPORTANT>

## Core Principle

Review is not a ceremony. It is an independent check against the request, the accepted plan, the diff, and the evidence.

The reviewer must receive focused context, not the full chat history. A strong review packet lets the reviewer find real issues without reconstructing the whole session.

## Use When

- Implementation is complete enough for review.
- The user asks for review, audit, PR readiness, merge readiness, or final inspection.
- Medium or large work needs a holistic review before quality gate.
- A subagent task or plan slice has finished and should be checked before the next slice.
- A complex bugfix has proof but still needs a fresh perspective.
- You are stuck and a static independent pass could reveal a missed assumption.

## Do Not Use When

- The user is giving review feedback; use `forge-receiving-code-review`.
- The task still has no implementation evidence.
- The next step is debugging a failure; use `forge-systematic-debugging`.
- The change is so small and low-risk that review would add no signal; still use `forge-verification-before-completion` before claiming done.

## When Review Is Mandatory

Request review before:

- merge, PR readiness, release readiness, or "ready" claims
- medium or large feature completion
- broad refactors or cross-package changes
- security, auth, payment, install, release, rollback, or data migration changes
- final integration after subagent-driven or parallel-agent execution

Review after each medium+ subagent slice when that slice can accumulate defects into later work.

## Review Packet

- review scope
- User request and non-goals
- Changed files or artifact paths
- Relevant diff or summary
- Verification already run
- Known residual risk
- Specific questions for the reviewer

## Strong Review Packet Template

```text
Review scope:
- <files, package, artifact, PR, or slice>

What changed:
- <concise implementation summary>

Source request / accepted plan:
- <requirement, spec, plan task, or user instruction>

Non-goals:
- <what should not be reviewed as required scope>

Diff range or artifacts:
- Base: <base sha, branch, or before artifact>
- Head: <head sha, branch, or after artifact>
- Files/artifacts: <paths>

Verification already run:
- <commands/checks and latest result>

Known residual risk:
- <unverified areas, skipped checks, assumptions>

Reviewer questions:
- <specific concerns to inspect>
```

Use SHAs when available. Use explicit artifact paths when the review is docs, generated output, release bundle, or non-git state.

## Review Rules

- Findings first, ordered by severity.
- If no findings, state scope and residual testing gaps.
- Static-only review must say static-only.
- Do not approve from vibes or previous results.
- For medium or large work, final review must be separate from implementation rhythm.

## Severity Contract

Ask the reviewer to classify issues:

- `Critical`: unsafe to proceed; correctness, data loss, security, broken build, or severe regression.
- `Important`: should fix before ready/merge; meaningful maintainability, coverage, integration, or requirement gap.
- `Minor`: useful cleanup that should not block unless the user wants polish.
- `Question`: unclear requirement, tradeoff, or scope issue requiring a decision.

Critical and Important findings require disposition before proceeding.

## Requesting A Subagent Review

When the host supports reviewer lanes:

1. Give the reviewer the packet, not the whole conversation.
2. Tell them to review spec compliance before code quality if the work came from a plan.
3. Tell them to report findings first, ordered by severity.
4. Tell them to include file paths and tight line references when possible.
5. Tell them not to rewrite the implementation unless specifically assigned a fix lane.

For final review after multiple slices, include the ownership map, all reviewer dispositions, and the final verification evidence.

## Acting On Review Results

- Fix Critical findings immediately or stop and escalate.
- Fix Important findings before ready/merge claims unless the user explicitly accepts the risk.
- Track Minor findings separately if they are not blocking.
- Challenge findings that are technically wrong, out of scope, or contradicted by evidence.
- Re-run the relevant proof after fixes.
- Request re-review for any fixed Critical or Important finding that could still be misunderstood.

## Disposition

Return one of:

- `ready-for-quality-gate`
- `changes-required`
- `blocked-by-residual-risk`

Then use `forge-verification-before-completion` before any ready, done, or merge claim.

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "The tests passed, so review is unnecessary." | Tests are evidence, not holistic review. |
| "The reviewer can infer the plan." | Missing context produces shallow review. |
| "No findings means done." | Quality gate still needs fresh verification. |
| "Important findings can wait." | Important findings require disposition before ready/merge. |
| "The reviewer should see everything." | Focused packets produce better review than full-history dumps. |

## Integration

- Called by: `forge-executing-plans`, `forge-subagent-driven-development`, and `forge-systematic-debugging` after implementation proof exists.
- Calls next: `forge-receiving-code-review` when findings arrive, then `forge-verification-before-completion` before any success claim.
- Pairs with: `forge-finishing-a-development-branch` for post-review branch resolution.
