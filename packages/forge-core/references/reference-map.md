# Forge Reference Map

> Goal: help maintainers and agents read the right current document or reference instead of searching the entire repo.

## Source Repo Current Docs

| File | When to read |
| --- | --- |
| docs/current/architecture.md | Current maintainer view of package boundaries, archive policy, and the maintenance-only posture |
| docs/current/operator-surface.md | Current source-repo operator contract, `repo_operator.py`, and dispatcher behavior |
| docs/current/install-and-activation.md | Current source-repo versus installed-runtime guidance, activation rules, and rollout sync |
| docs/archive/INDEX.md | Find historical plans and specs after they leave the active reading path |

## Reference Registry

| File | When to read |
| --- | --- |
| `smoke-tests.md` | Smoke-test host routing and Forge's general behavior |
| `smoke-test-checklist.md` | Record smoke-test results for each case |
| `constitution-lite.md` | Record or reuse repo-local principles without adding a heavier governance artifact |
| `target-state.md` | Re-anchor Forge strategy and operator choices to the north-star target state, including the shipped `1.15.x` closure target, the `1.16.x` surface-slim closure, and the current maintenance boundary |
| `execution-delivery.md` | Select execution mode, checkpoint, and completion state for large builds |
| `backend-briefs.md` | Validate or interpret persisted backend brief artifacts that already exist in the repo |
| `failure-recovery-playbooks.md` | Use when the chain is stalled, a gate is blocked, review is deadlocked, or deployment fails and you need a clear recovery path |
| `frontend-stack-profiles.md` | Choose stack lens for UI implementation or visualization |
| `ui-quality-checklist.md` | Quick review of UI anti-patterns and delivery criteria |
| `ui-escalation.md` | Decide when to pull more `$ui-ux-pro-max` |
| `ui-good-bad-examples.md` | Concrete good/bad patterns so the agent does not have to infer anti-patterns alone |
| `ui-heuristics.md` | Global heuristics for touch-heavy, dashboard, dense-data UI |
| `ui-progress.md` | Track progress for long UI tasks |
| `ui-briefs.md` | Validate or interpret persisted UI brief artifacts that already exist in the repo |
| `architecture-layers.md` | When deciding whether a capability belongs in core, generated artifacts, or workflow state |
| `extension-presets.md` | When defining bounded packet templates, workflow overlays, or planning presets without weakening core contracts |
| `kernel-tooling.md` | When you need the current kernel-only tooling surface, artifact paths, and verification entrypoints |
| `personalization.md` | When editing response-style preferences, adaptive language, or adapter wrappers for customization |
| `workspace-init.md` | When editing the skeleton workspace, init flow, or onboarding wrapper while preserving the repo-neutral contract |
| `help-next.md` | When editing navigator logic for help or next, repo-state priority, or operator guidance wrappers |
| `run-guidance.md` | When editing workflow `run`, ready-signal detection, command classification, or adapter wrappers for execute-then-route |
| `error-translation.md` | When fixing database error patterns, sanitation rules, or how `run` or `debug` converts technical errors into readable guidance |
| `bump-release.md` | When editing version-bump checklist, semver math, or release artifact update flow |
| `rollback-guidance.md` | When editing rollback planning, risk framing, or recovery strategy selection |
| `companion-skill-contract.md` | Design or update companion skills when the repo really has an extended runtime or framework layer |
| `companion-routing-smoke-tests.md` | Check routing between Forge and companion skills when the workspace uses a companion or local layer |

## Historical Planning Context

| File | When to read |
| --- | --- |
| docs/plans/forge_refactor_V3.md | Read only when the completed kernel-only contraction tranche itself matters as historical context |

## Reading Order

### When maintaining Forge core

```text
1. docs/current/architecture.md
2. docs/current/operator-surface.md if the change touches the source-repo entry contract
3. target-state.md if the change affects Forge strategy, process weight, verification strictness, or core identity
4. architecture-layers.md before moving ownership between core, generated artifacts, and workflow state
5. extension-presets.md when adding bounded packet template, workflow overlay, or planning preset contracts
6. docs/current/install-and-activation.md if the change touches build/install/activation guidance
7. kernel-tooling.md if you need deterministic preview or check scripts instead of plain prose
8. personalization.md if you are editing response style or preference engine
9. workspace-init.md if editing init or onboarding skeleton logic
10. help-next.md if editing navigator help or next
11. run-guidance.md if editing run or execute-then-route
12. error-translation.md if you are editing error translator or helper layers
13. bump-release.md or rollback-guidance.md if editing release operators
14. execution-delivery.md depending on the layer being edited
15. smoke-tests.md or smoke-test-checklist.md if needed to verify host behavior
16. docs/archive/INDEX.md only when historical context is truly needed
```

### When the repo does not have local skills

```text
1. SKILL.md
2. plan.md / architect.md / build.md / debug.md / review.md depending on intent
3. execution-delivery.md or quality-gate.md if the task is long or risky
```

### When you just want to smoke test Forge core

```text
1. smoke-tests.md
2. smoke-test-checklist.md
```

### When debugging companion routing

```text
1. companion-skill-contract.md
2. companion-routing-smoke-tests.md
3. kernel-tooling.md if you need to run checker
```

### When designing a workspace according to the global plus local model

```text
1. companion-skill-contract.md
2. kernel-tooling.md
3. companion-routing-smoke-tests.md
4. smoke-tests.md if you need to verify host behavior more broadly
```

### When doing implementation after plan or design

```text
1. docs/current/operator-surface.md if the change touches source-repo routing or wrappers
2. target-state.md if the change affects Forge process direction or strictness
3. execution-delivery.md
4. build.md when defining or updating the canonical build packet
5. test.md when the proof chain or browser QA evidence changes
6. debug.md when reproduction or root-cause packet changes
7. failure-recovery-playbooks.md if the chain has risk stall or block
8. kernel-tooling.md if checkpoint artifact is needed
9. review.md if you need to clear disposition last
10. quality-gate.md if you need to go or no-go clearly before claiming or deploying
```

### When doing release-critical flow

```text
1. docs/current/install-and-activation.md
2. secure.md
3. quality-gate.md
4. deploy.md
5. failure-recovery-playbooks.md if the gate is blocked or rollout fails
6. execution-delivery.md if the chain is long or high-risk
```

### When validating maintenance-only posture

```text
1. target-state.md to confirm the `1.15.x` closure target, the `1.16.x` surface-slim closure, the maintenance boundary, and reopen criteria
2. docs/current/architecture.md to confirm the live maintainer surface stays in current docs instead of roadmap files
3. bump-release.md if the stable version line or release-note surface changes
4. kernel-tooling.md if you need deterministic checks to keep release-facing docs and generated artifacts aligned
5. docs/archive/INDEX.md if you need to map the resulting historical plan inventory
```

### When working on backend tasks

```text
1. build.md
2. plan.md when scope, compatibility, or verification is not locked
3. architect.md when system shape or boundaries need design
4. execution-delivery.md if the backend task spans multiple checkpoints
5. failure-recovery-playbooks.md if the task is migration, recovery, or release-sensitive
6. kernel-tooling.md if you need deterministic packet or verification helpers
7. companion-skill-contract.md if the runtime or framework is clear and you want to add more layers
```

### When doing frontend or visualization

```text
1. frontend-stack-profiles.md
2. ui-quality-checklist.md
3. ui-good-bad-examples.md
4. ui-heuristics.md
5. ui-escalation.md if the visual guide is too open
6. ui-progress.md if the task takes a long time
7. kernel-tooling.md if you want deterministic artifact or verification helpers
```

### When stalled or blocked

```text
1. failure-recovery-playbooks.md
2. execution-delivery.md if you need to look back at the chain or checkpoint
3. kernel-tooling.md if you need to capture new artifacts
4. debug.md / quality-gate.md / review.md / deploy.md depending on where you are stuck
```
