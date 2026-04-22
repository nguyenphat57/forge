---
name: forge-writing-plans
description: Use when an approved design, clear requirement, or multi-step implementation needs a written executable plan before code.
---

# Forge Writing Plans

<EXTREMELY-IMPORTANT>
Use this before touching code when implementation needs more than a single mechanical edit.

No build without a written implementation plan and execution choice.
</EXTREMELY-IMPORTANT>

## Use When

- A design or spec is approved and the next step is implementation planning.
- The user asks for a plan, checklist, task breakdown, or execution strategy.
- The work spans multiple files, behaviors, tests, artifacts, or verification steps.

## Do Not Use When

- The task is pure one-line mechanical upkeep with no behavior or risk.
- The request is still open-ended; use `forge-brainstorming` first.
- The user already supplied a complete executable plan and wants execution.

## Plan File

Write or update:

```text
docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md
```

Every plan starts with:

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [...]
**Architecture:** [...]
**Tech Stack:** [...]
```

## Required Structure

- Source and current state
- Desired end state
- Out of scope
- File structure and responsibility map
- Implementation tasks
- Acceptance criteria
- Verification
- Risks and rollback
- Execution mode

## File Structure

Before defining tasks, map which files will be created or modified and what each one is responsible for.

- Lock decomposition before task writing. Do not let file boundaries emerge accidentally halfway through the plan.
- Prefer units with one clear responsibility and explicit interfaces.
- Files that change together should usually live together.
- In an existing codebase, follow established patterns unless the design explicitly changes them.
- If a file is already overloaded and the current work depends on it, it is valid for the plan to include a focused split or cleanup.

This structure should make each later task feel mechanically obvious instead of architecturally ambiguous.

## Bite-Sized Task Granularity

Each step is one action. Aim for a task shape that a fresh worker can execute with minimal interpretation.

Good granularity looks like:

- write the failing test
- run it to verify RED
- write the minimum implementation
- rerun the targeted proof
- run the named baseline
- commit or checkpoint

Do not compress multiple behaviors, files, or proof moves into one step just because they seem related.

## Task Quality

- Each step should be one small action.
- Include exact files and commands whenever knowable.
- Start behavior changes with a failing test or failing content check.
- Include expected RED and GREEN output.
- Include a full check appropriate to blast radius.
- Avoid TODO, TBD, "handle edge cases", "add validation", or "similar to above".
- Preserve type, method signature, and property name consistency across the whole plan.

## Task Template

Use a consistent checkbox task format:

```markdown
### Task N: Component or slice name

- [ ] Step 1: Write the failing test or failing content check
  - Files: `tests/path/test_file.py`, `src/path/file.py`
  - Change: define the missing behavior under proof
  - Proof: `pytest tests/path/test_file.py -q` -> FAIL for the expected reason
  - Notes: name the exact behavior and keep the scope narrow

- [ ] Step 2: Implement the minimum code
  - Files: `src/path/file.py`
  - Change: add only the code needed for the RED proof
  - Proof: rerun the exact targeted command first
  - Notes: no opportunistic refactors in this step

- [ ] Step 3: Run the broader baseline
  - Files: none
  - Change: verify surrounding behavior still holds
  - Proof: exact baseline command
  - Notes: name residual risk if the baseline cannot run
```

Every implementation task should be specific enough that a fresh worker can execute it without inventing file scope, proof, or intent.

## No Placeholders

These are plan failures, not harmless shorthand:

- `TODO`, `TBD`, `implement later`, `fill in details`
- "add appropriate validation", "handle edge cases", or "write tests" without exact proof content
- "same as above" or "similar to Task N"
- references to functions, types, commands, or files that are never defined elsewhere in the plan
- code-changing steps that omit the affected files, proof, or expected result

If a task cannot be written concretely yet, the plan is not ready.

## Plan Self-Review

Before handing the plan to execution, review it for:

- placeholders such as `TODO`, `TBD`, "fill in later", or vague references
- missing file scope, command details, or proof expectations
- steps that bundle multiple behaviors into one task
- inconsistent naming between spec, files, and planned changes
- missing rollback or residual-risk notes where blast radius is non-trivial
- gaps between spec requirements and planned tasks

## Execution Choice Gate

Stop after the plan with:

```text
Plan complete and saved to `docs/plans/...`. Choose execution mode:
1. Subagent-Driven - use forge-subagent-driven-development
2. Inline Execution - use forge-executing-plans
```

Do not start build until the user chooses or has already instructed the mode.

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "The plan is obvious." | Obvious tasks still need exact proof and file scope. |
| "I can plan while coding." | That hides missing proof and scope decisions. |
| "Use another skill family here." | Forge plans reference Forge skills, not external skill names. |
| "The worker can figure out placeholders later." | Placeholder leak creates inconsistent execution packets. |

## Integration

- Called by: `forge-brainstorming` after the design is approved, or directly by the user when requirements are already locked.
- Calls next: `forge-subagent-driven-development` or `forge-executing-plans`, depending on the chosen execution mode.
- Pairs with: `forge-session-management` for saving plan state and `forge-verification-before-completion` for end-of-plan closeout.

Shared scripts and references live in the installed Forge orchestrator bundle.
