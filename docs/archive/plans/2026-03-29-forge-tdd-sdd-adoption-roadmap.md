# Forge TDD/SDD Adoption Roadmap

Date: 2026-03-29
Status: historical proposal, superseded by `docs/plans/2026-03-29-forge-process-first-implementation-plan.md` and `docs/plans/2026-04-02-forge-1.15.x-maintenance-closure.md`
Depends on: `docs/PROJECT_TDD_SDD_BENCHMARK_2026-03-29.md`

## Goal

Raise Forge from:
- verification-first with partial process artifacts

To:
- artifact-driven for brownfield work
- harder to rationalize around TDD
- clearer spec quality gates before build
- stronger end-to-end evidence before claims

## Operating Principle

Do not replace Forge with another framework.

Adopt:
- `OpenSpec` for artifact spine
- `Superpowers` for execution rigor
- `Spec Kit` for spec quality control

Keep:
- Forge's verification gate
- Forge's routing model
- Forge's quality-gate and residual-risk reporting

## Scope In

- change artifacts
- spec delta handling
- verify-against-artifacts workflow
- worktree bootstrap and baseline proof
- stronger TDD wording and packets
- clarification and checklist layer
- repo-local constitution-lite support

## Scope Out

- full Spec Kit lifecycle adoption
- full OpenSpec command surface adoption
- turning Forge into a skills marketplace product
- heavy markdown ceremony for small work

## Delivery Shape

Use `P1/P2/P3` with each phase independently valuable.

Order:
1. `P1` artifact spine
2. `P2` execution rigor
3. `P3` spec quality control

## P1: Artifact Spine

### Objective

Make Forge changes durable enough that a medium or large slice has:
- intent
- design
- tasks
- verification
- spec delta

### Why First

Without this, Forge still relies too much on chat context and generalized plans.

### Main Outcomes

- Add `specs/` under active change artifacts
- Add first-class `verify-change`
- Merge archived deltas back into durable specs or a durable spec index

### Files To Update

Existing files:
- `packages/forge-core/scripts/change_artifacts.py`
- `packages/forge-core/scripts/change_artifacts_paths.py`
- `packages/forge-core/scripts/change_artifacts_archive.py`
- `packages/forge-core/scripts/change_artifacts_status.py`
- `packages/forge-core/scripts/record_quality_gate.py`
- `packages/forge-core/workflows/execution/change.md`
- `packages/forge-core/workflows/execution/quality-gate.md`
- `packages/forge-core/tests/test_change_artifacts.py`
- `packages/forge-core/tests/test_quality_gate.py`

New files:
- `packages/forge-core/scripts/verify_change.py`
- `packages/forge-core/workflows/execution/verify-change.md`
- `packages/forge-core/tests/test_verify_change.py`

### Required Behavior

Active change layout should become:
- `proposal.md`
- `design.md`
- `tasks.md`
- `verification.md`
- `resume.md`
- `specs/<topic>/spec.md`
- `status.json`

`verify-change` should score:
- completeness
- correctness
- coherence
- evidence strength
- residual risk

### Routing Changes

Update:
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/scripts/route_analysis.py`
- `packages/forge-core/data/orchestrator-registry.json`

So that:
- medium and large build work can require `verify-change` before final `quality-gate`
- review and release paths can consume `verify-change` output

### Verification

Minimum proof:
- `python -m pytest packages/forge-core/tests/test_change_artifacts.py packages/forge-core/tests/test_quality_gate.py packages/forge-core/tests/test_verify_change.py`

Docs/content proof:
- confirm `change.md` and `quality-gate.md` reference `specs/` and `verify-change`

### Exit Criteria

- Forge can reopen a medium or large change from artifacts alone
- Forge can compare code against change artifacts, not only against tests
- archive preserves spec delta history and durable verification state

## P2: Execution Rigor

### Objective

Make Forge harder to drift during build work by adding:
- worktree bootstrap
- cleaner proof-before-progress packets
- stronger TDD anti-rationalization
- clearer reviewer-lane sequencing

### Main Outcomes

- canonical worktree helper for risky work
- baseline verification before editing
- sharper RED-before-GREEN reset rules
- spec-compliance review before code-quality review in independent lanes

### Files To Update

Existing files:
- `packages/forge-core/workflows/execution/build.md`
- `packages/forge-core/workflows/execution/test.md`
- `packages/forge-core/workflows/design/spec-review.md`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/scripts/route_delegation.py`
- `packages/forge-core/scripts/track_execution_progress.py`
- `packages/forge-core/references/execution-delivery.md`
- `packages/forge-core/tests/test_route_preview.py`

New files:
- `packages/forge-core/scripts/prepare_worktree.py`
- `packages/forge-core/tests/test_prepare_worktree.py`

### Required Behavior

`prepare_worktree.py` should:
- choose or create isolated worktree path
- verify ignore safety for project-local worktree roots
- run project setup if needed
- run baseline command or suite
- return ready or blocked state with evidence

`build.md` and `test.md` should gain:
- clearer reset conditions when RED was skipped
- stronger examples of invalid rationalization
- stricter distinction between `slice proof`, `boundary proof`, and `broader proof`

`route_preview.py` should:
- recommend worktree by default for medium+ behavioral work in dirty repos
- expose this recommendation cleanly in route output

### Verification

Minimum proof:
- `python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_prepare_worktree.py`

Regression proof:
- rerun existing targeted suites that cover delegation and quality handoff if touched

### Exit Criteria

- risky build work can start from a clean isolated baseline
- Forge's TDD guidance is explicit enough that skipping RED is clearly treated as invalid
- reviewer lanes operate in a stricter order: spec compliance first, quality second

## P3: Spec Quality Control

### Objective

Improve the quality of the packet before build starts so medium and risky work arrives at `plan` or `spec-review` with fewer hidden assumptions.

### Main Outcomes

- clarification markers
- requirements checklist
- constitution-lite artifact
- pre-plan or pre-spec-review quality pass

### Files To Update

Existing files:
- `packages/forge-core/workflows/design/brainstorm.md`
- `packages/forge-core/workflows/design/plan.md`
- `packages/forge-core/workflows/design/spec-review.md`
- `packages/forge-core/scripts/initialize_workspace.py`
- `packages/forge-core/scripts/capture_continuity.py`
- `packages/forge-core/tests/test_initialize_workspace.py`

New files:
- `packages/forge-core/scripts/generate_requirements_checklist.py`
- `packages/forge-core/scripts/check_spec_packet.py`
- `packages/forge-core/tests/test_generate_requirements_checklist.py`
- `packages/forge-core/tests/test_check_spec_packet.py`
- `packages/forge-core/references/constitution-lite.md`

### Required Behavior

Clarification layer:
- mark unresolved assumptions explicitly
- surface them before `plan` or `spec-review`

Checklist layer:
- validate requirements for ambiguity, measurability, and testability

Constitution-lite:
- repo-local file with testing, compatibility, simplicity, and review rules
- opt-in for existing repos
- scaffolded by workspace init when requested

### Verification

Minimum proof:
- `python -m pytest packages/forge-core/tests/test_initialize_workspace.py packages/forge-core/tests/test_generate_requirements_checklist.py packages/forge-core/tests/test_check_spec_packet.py`

Content proof:
- `brainstorm.md`, `plan.md`, and `spec-review.md` reference clarification and checklist use

### Exit Criteria

- medium or risky work can fail early on poor spec quality
- repo-local principles can shape planning without forcing heavy ceremony
- Forge has a durable pre-build quality layer, not only a post-build evidence layer

## Decision Gates

Do not start `P2` until:
- `P1` artifact format is stable enough to support `verify-change`

Do not start `P3` constitution-lite scaffolding until:
- clarification and checklist behavior are proven useful without adding too much ceremony

## Success Metrics
- After `P1`: medium and large changes can be resumed from files alone
- After `P2`: route output and execution packets recommend isolation and proof order consistently
- After `P3`: fewer medium/risky tasks reach build with unresolved ambiguity

## First Files To Touch

If starting immediately, the best first file order is:
1. `packages/forge-core/scripts/change_artifacts.py`
2. `packages/forge-core/scripts/change_artifacts_paths.py`
3. `packages/forge-core/workflows/execution/change.md`
4. `packages/forge-core/scripts/verify_change.py`
5. `packages/forge-core/tests/test_verify_change.py`
6. `packages/forge-core/workflows/execution/quality-gate.md`
7. `packages/forge-core/scripts/route_preview.py`
8. `packages/forge-core/workflows/execution/test.md`
9. `packages/forge-core/workflows/execution/build.md`
10. `packages/forge-core/workflows/design/spec-review.md`

## Bottom Line

If Forge implements only `P1`, it becomes materially more artifact-driven.

If Forge implements `P1 + P2`, it becomes much harder to drift in real execution.

If Forge implements all `P1 + P2 + P3`, it becomes a stronger hybrid:
- spec-aware before build
- disciplined during build
- evidence-backed at handoff
