# Forge Reference Map

> Goal: send maintainers and agents to the current split-skill, markdown-first contract quickly, without teaching obsolete public surfaces.

## Current Docs First

| File | When to read |
| --- | --- |
| `docs/current/architecture.md` | Understand live package boundaries, sibling skill activation, and public-versus-internal surface split |
| `docs/current/operator-surface.md` | Understand the thin operator contract, the 1% rule, and `help`/`next` audit sidecars |
| `docs/current/install-and-activation.md` | Understand sibling skill installation, generated-host-artifact boundaries, and source-versus-installed ownership |
| `docs/archive/INDEX.md` | Find historical plans and specs only when historical context is actually needed |

## Skill Sources

| Path | When to read |
| --- | --- |
| `packages/forge-core/SKILL.md` | Change the host-neutral bootstrap, 1% rule, or invariant boundary wording |
| `packages/forge-core/skills/` | Change canonical process behavior for Forge sibling skills |
| `packages/forge-core/workflows/` | Repair operator/session compatibility wrappers only; these files are not the source of truth |
| `packages/forge-codex/overlay/SKILL.md` | Change Codex bootstrap access wording without forking skill meaning |
| `packages/forge-antigravity/overlay/SKILL.md` | Change Antigravity bootstrap access wording without forking skill meaning |

## Core References

| File | When to read |
| --- | --- |
| `target-state.md` | Re-anchor strategy, public contract limits, invariant boundaries, and what changes qualify as drift correction versus product expansion |
| `kernel-tooling.md` | Use deterministic scripts for invariants, workflow-state, and preferences without turning them into the public contract |
| `personalization.md` | Edit or reason about response preferences, language handling, or preference persistence |
| `help-next.md` | Change `help` or `next` while keeping them artifact-backed audit sidecars instead of primary control surfaces |
| `run-guidance.md` | Change `run` while preserving execute-then-route from evidence |
| `workspace-init.md` | Change init or onboarding while keeping the bootstrap thin and skill-first |
| `architecture-layers.md` | Decide whether a capability belongs in sibling skill markdown, deterministic state tooling, or generated artifacts |
| `tdd-discipline.md` | Apply RED -> GREEN -> REFACTOR and the delete-before-implementation rule for behavioral work |
| `execution-delivery.md` | Shape medium or large execution flow without losing artifact-backed checkpoints |
| `subagent-execution.md` | Shape subagent-driven execution without reintroducing a parallel orchestration model |
| `subagent-prompts/final-reviewer-prompt.md` | Review final implementation quality when a split execution lane needs a final pass |
| `failure-recovery-playbooks.md` | Recover when a workflow, gate, or release path is blocked |
| `debugging/root-cause-tracing.md` | Trace a visible symptom backward to the original trigger before fixing |
| `debugging/defense-in-depth.md` | Add layered validation after root cause shows bad state crossed boundaries |
| `debugging/condition-based-waiting.md` | Replace flaky sleeps and guessed delays with bounded readiness conditions |
| `smoke-tests.md` | Smoke-test the live host and sibling skill contract |
| `smoke-test-checklist.md` | Record smoke-test outcomes and gaps |

## Design And Planning References

| File | When to read |
| --- | --- |
| `design/design-doc-template.md` | Write a brainstorm design doc |
| `design/design-review-checklist.md` | Self-review a design doc before asking for approval |
| `design/architectural-lens.md` | Reopen system-shape, ownership, and compatibility questions inside `brainstorm` without reviving a separate architecture workflow |
| `design/visual-companion-guidance.md` | Decide whether the optional visual lens helps without turning it into a default stage |
| `planning/implementation-plan-template.md` | Write an implementation plan after design approval |
| `planning/plan-self-review-checklist.md` | Review plan readiness before asking for execution choice |
| `planning/execution-handoff.md` | Record the execution-choice gate before `forge-executing-plans` |

## Adapter References

| File | When to read |
| --- | --- |
| `packages/forge-core/skills/writing-skills/SKILL.md` | Create, edit, absorb, harden, test, or deploy Forge sibling skills |
| `bump-release.md` | Edit release bump flow or semver guidance |
| `rollback-guidance.md` | Edit rollback planning and recovery framing |

## Reading Order

### When changing Forge core docs or public contract

```text
1. docs/current/architecture.md
2. docs/current/operator-surface.md
3. docs/current/install-and-activation.md
4. packages/forge-core/SKILL.md
5. packages/forge-core/skills/*/SKILL.md for affected processes
6. target-state.md
7. architecture-layers.md
8. kernel-tooling.md
9. docs/archive/INDEX.md only when historical context is necessary
```

### When changing skill activation or compatibility wrappers

```text
1. packages/forge-core/SKILL.md
2. packages/forge-core/skills/*/SKILL.md
3. docs/current/operator-surface.md
4. help-next.md or run-guidance.md if the change touches sidecars
5. target-state.md if the user-visible contract might shift
```

### When changing install, activation, or generated host artifacts

```text
1. docs/current/install-and-activation.md
2. docs/current/architecture.md
3. docs/architecture/generated-host-artifacts/*
4. packages/forge-codex/overlay/SKILL.md or packages/forge-antigravity/overlay/SKILL.md
5. kernel-tooling.md
6. personalization.md if preferences or bootstrap state are involved
```

### When verifying current contract alignment

```text
1. target-state.md
2. docs/current/architecture.md
3. docs/current/operator-surface.md
4. docs/current/install-and-activation.md
5. packages/forge-core/skills/*/SKILL.md
6. kernel-tooling.md
7. smoke-tests.md
8. smoke-test-checklist.md
```

### What Not To Teach First

```text
- Do not teach `route_preview` as the public interface.
- Do not teach generated host artifacts as the canonical wording source.
- Do not teach Python helpers first when the question is really about skill choice or control semantics.
- Do not teach `workflows/` files as the primary activation surface.
```

The current repo posture is split-skill markdown control with Python constrained to invariant boundaries.
