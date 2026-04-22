---
name: forge-executing-plans
description: Use when a written implementation plan exists and the user wants inline execution, code changes, or plan task completion.
---

# Forge Executing Plans

<EXTREMELY-IMPORTANT>
**REQUIRED GATE:** Use this before executing a written plan in the current session.

```text
NO PLAN EXECUTION WITHOUT SLICE-BY-SLICE PROOF
```

**REQUIRED SUB-SKILL:** If tasks are independent and subagents are useful, use `forge-subagent-driven-development` instead of improvising ad hoc delegation.
</EXTREMELY-IMPORTANT>

## Use When

- A written plan exists and the user says implement, continue, execute, build, or do it.
- The execution mode is inline, same-session, or tightly coupled.
- A compatibility `/code` alias points here.

## Do Not Use When

- No plan or spec exists for behavioral work; use `forge-brainstorming` or `forge-writing-plans`.
- The task is a bug or regression; use `forge-systematic-debugging` first.
- The main need is final claim or merge readiness; use `forge-verification-before-completion` and review skills.

## Process

1. Load the plan and review it critically.
2. Identify blockers, missing files, missing proof, or scope conflicts **before editing**.
3. Define verification before each slice.
4. If behavior changes and a harness is viable, **invoke `forge-test-driven-development` before implementation code**.
5. If the repo is dirty or the plan needs isolation, **invoke `forge-using-git-worktrees` before editing**.
6. Execute one task or slice at a time.
7. Run the exact proof for that slice before proceeding.
8. Update workflow-state for medium, risky, or long-running work via the orchestrator bundle scripts.
9. **Do not claim ready or done** until `forge-verification-before-completion` has been invoked.

## Execution Loop

For each task or slice:

1. Mark the current slice clearly.
2. Follow the plan steps exactly unless a real blocker or plan error appears.
3. Run the named proof for that slice.
4. If the proof fails unexpectedly, stop and classify the problem instead of free-styling.
5. Record the new state before moving to the next slice.

**DO NOT BATCH** several slices together just because they share files.

## Execution Discipline

- Do not combine unrelated plan tasks for convenience.
- Do not skip RED when TDD applies.
- Do not swap final verification to a weaker check.
- Stop and return to planning if the plan is wrong, ambiguous, or needs new scope.
- Keep user edits and unrelated dirty work intact.

## Stop And Ask For Help

**STOP EXECUTING IMMEDIATELY** when:

- a blocker prevents safe progress
- the plan has a critical gap that prevents starting or continuing
- the instruction is unclear enough that guessing would change scope
- the same verification fails repeatedly without a clear root cause

**DO NOT PUSH THROUGH BY INSTINCT.** Ask for clarification or return to the earlier process skill.

## Reopen Earlier Steps

**RETURN TO PLAN REVIEW BEFORE CONTINUING** when:

- the partner updates the plan
- the current slice reveals a missing boundary decision
- the implementation path now needs new scope, new files, or a stronger proof shape

Return to `forge-writing-plans` if the plan itself must change. Return to `forge-systematic-debugging` if the failure is really a defect investigation.

## Completion Handoff

After all slices are complete and verified:

- **REQUIRED:** invoke `forge-requesting-code-review` when review is still needed
- **REQUIRED:** invoke `forge-verification-before-completion` before any ready or done claim
- **REQUIRED:** invoke `forge-finishing-a-development-branch` when the work is truly ready for merge, PR, keep, or discard decisions

## Integration

- Called by: `forge-writing-plans` after the user chooses inline execution, and by `forge-session-management` when resuming an approved plan.
- Calls next: `forge-test-driven-development`, `forge-using-git-worktrees`, `forge-requesting-code-review`, `forge-verification-before-completion`, and `forge-finishing-a-development-branch` as the slice demands.
- Pairs with: `forge-subagent-driven-development` for delegated execution and `forge-systematic-debugging` when proof fails unexpectedly.

## Handoff

Report:

- Plan path
- Task or slice completed
- Files changed
- Verification run and result
- Current state: `in-progress`, `ready-for-review`, or `blocked-by-residual-risk`
- Next skill if needed

Shared scripts and references live in the installed Forge orchestrator bundle.
