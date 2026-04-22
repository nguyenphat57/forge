# Implementation Plan Template

Use for Forge `plan` outputs.

Path:

```text
docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md
```

Template:

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

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

- Subagent-Driven: [...]
- Inline Execution: [...]
- execution choice: pending
```

Reject placeholders such as `TBD`, `TODO`, "handle edge cases", "write tests for the above", or "similar to Task N". Complete code in every step that changes code.
