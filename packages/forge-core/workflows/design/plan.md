---
name: plan
type: flexible
triggers:
  - intent: BUILD
  - approved design doc exists
  - user asks for implementation plan
  - shortcut: /plan
quality_gates:
  - Implementation plan is written to docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md
  - Plan follows the Superpowers writing-plans checklist format
  - Plan starts with the agentic-worker header
  - No placeholders, TODOs, or vague implementation tasks remain
  - Every slice has tests or proof commands
  - Plan includes execution choice before build
  - Build does not start until the user chooses an execution mode
---

# Plan - Implementation Plan Writer

## The Iron Law

```text
NO BUILD WITHOUT A WRITTEN IMPLEMENTATION PLAN AND EXECUTION CHOICE
```

`plan` is Forge's version of Superpowers `writing-plans`. It turns an approved design or clear user request into an executable checklist. It does not brainstorm alternative designs.

Write plans as if the implementer is skilled but has zero context for this codebase. Give exact files, exact commands, expected outcomes, code snippets, tests, docs, and commit points. Use DRY, YAGNI, TDD, and frequent commits.

## Hard Gate

Use this workflow for every `BUILD` route.

Rules:
- always write or update a plan file, even for small work
- inherit the approved design from `brainstorm` when one exists
- if behavior or visual design is not approved, return to `brainstorm`
- if system shape needs deeper analysis, mark `architect` as an optional lens instead of inserting it into the default route
- stop at execution choice before `build`

## Required Output File

Write implementation plans here:

```text
docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md
```

Use this title:

```markdown
# [Feature Name] Implementation Plan
```

Every plan MUST start with this header:

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about the approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## File Structure

Before defining tasks, map the files that will be created or modified and what each file is responsible for.

Rules:
- every file should have one clear responsibility
- follow existing codebase patterns
- split by responsibility, not by technical layer
- include targeted cleanup only when it serves the current goal
- exact paths are required whenever they can be known

This file map locks the task decomposition. Do not write tasks until the likely file/surface boundaries are clear enough.

## Bite-Sized Task Granularity

Each step is one action (2-5 minutes).

Good steps:
- Write the failing test
- Run test to verify it fails
- Implement the minimal passing change
- Run test to verify it passes
- Commit

Bad steps:
- Build the feature
- Add validation and edge cases
- Clean up everything
- Test the above

## Required Plan Structure

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about the approach]

**Tech Stack:** [Key technologies/libraries]

---

## Source And Current State

- Source design: docs/specs/YYYY-MM-DD-<topic>-design.md
- Existing behavior: [...]
- Relevant files: [...]
- Relevant tests: [...]
- Baseline command: [...]

## Desired End State

- [...]

## Out Of Scope

- [...]

## Implementation Tasks

### Task 1: [Component Name]

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing_file.py`
- Test: `tests/exact/path/test_file.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function_under_test("input")
    assert result == "expected"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/exact/path/test_file.py::test_specific_behavior -v`
Expected: FAIL because the behavior is not implemented.

- [ ] **Step 3: Write minimal implementation**

```python
def function_under_test(value):
    return "expected"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/exact/path/test_file.py::test_specific_behavior -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/exact/path/test_file.py exact/path/to/new_file.py
git commit -m "feat: add specific behavior"
```

## Acceptance Criteria

- [...]

## Verification

- Red test command: [...]
- Green test command: [...]
- Full check: [...]

## Risks And Rollback

- Risk: [...]
- Mitigation: [...]
- Rollback: [...]

## Execution Mode

- Subagent-Driven: use when the plan has independent tasks that can be safely split.
- Inline Execution: use when the plan is small, tightly coupled, or the host lacks useful delegation.
- execution choice: the user must choose Subagent-Driven or Inline Execution before `build`.
```

## Required Sub-Skill Line

Every plan must include:

```text
REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans
```

If Inline Execution is chosen later, keep the line and execute through `superpowers:executing-plans`.

## Planning Rules

- Make each task small enough to execute in one focused pass.
- Put exact file or module boundaries on each step whenever known.
- Start implementation with a failing test or failing content check.
- Do not include vague tasks such as "polish", "cleanup", or "handle edge cases" without proof.
- Include commands that prove the current step and the full change.
- Include rollback or recovery when state, migration, release, or public behavior changes.
- Avoid re-comparing design options unless the design's reversal signal fired.

## No Placeholders

Every step must contain the actual content an engineer needs.

Plan failures:
- `TBD`, `TODO`, `implement later`, or `fill in details`
- "Add appropriate error handling"
- "Add validation"
- "Handle edge cases"
- "Write tests for the above"
- "Similar to Task N"
- references to functions, types, or files not defined in the plan

Complete code in every step that changes code. If a step writes or edits code, show the code or the exact diff shape needed. If a step runs a command, include the exact command and expected output.

## Execution Choice Gate

The final output of `plan` is not `build`. The final output is an execution choice.

After writing and reviewing the plan, stop with:

```text
Plan complete and saved to `docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
```

Record the stage decision as:

```text
decision: execution-choice-required
next_action: Choose Subagent-Driven or Inline Execution before build.
```

`next` must keep focus on `plan` while this decision is pending.

## Plan Self-Review

Before handoff, review the plan:
- Does every implementation step have a proof?
- Is the first step a failing test or failing check?
- Are files and boundaries specific enough for implementation?
- Do types, method signatures, and property names match across tasks?
- Is type, method signature, and property name consistency maintained across the whole plan?
- Are design assumptions inherited rather than re-decided?
- Are risky areas paired with rollback or recovery guidance?
- Is the execution choice explicit?

If any answer is no, revise the plan before asking for execution choice.

## Activation Announcement

```text
Forge: plan | write implementation plan and request execution choice
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: plan`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.
