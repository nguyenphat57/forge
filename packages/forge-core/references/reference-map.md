# Forge Reference Map

> Goal: help maintainers and agents know which reference to read for the right job, instead of searching the entire `references/` directory.

## Reference Registry

|File | When to read|
|------|-------------|
|`smoke-tests.md` | Smoke-test host routing and Forge's general behavior|
|`smoke-test-checklist.md` | Record smoke-test results for each case|
|`backend-briefs.md` | Create or reuse a backend brief for medium/large API, job, event, or data changes|
|`artifact-driven-change-flow.md` | Run the full P1-P3 artifact-driven flow for medium/risky build work|
|`constitution-lite.md` | Record or reuse repo-local principles without adding a heavier governance artifact|
|`target-state.md` | Re-anchor Forge maintenance and operator choices to the north-star product target state|
|`execution-delivery.md` | Select execution mode, checkpoint, and completion state for large builds|
|`failure-recovery-playbooks.md` | Use when the chain is stalled, a gate is blocked, review is deadlocked, or deployment fails and you need a clear recovery path|
|`ui-briefs.md` | Use when frontend/visualize needs a first artifact before coding or mockups|
|`frontend-stack-profiles.md` | Choose stack lens for frontend or visualization|
|`ui-quality-checklist.md` | Quick review of UI anti-patterns and delivery criteria|
|`ui-escalation.md` | Decide when to pull more `$ui-ux-pro-max`|
|`ui-good-bad-examples.md` | Concrete good/bad patterns so the agent does not have to infer anti-patterns alone|
|`ui-heuristics.md` | Global heuristics for touch-heavy, dashboard, dense-data UI|
|`ui-progress.md` | Track progress for long UI tasks|
|`architecture-layers.md` | When deciding whether a capability belongs in core, generated artifacts, workflow state, or runtime tools|
|`extension-presets.md` | When defining bounded packet templates, workflow overlays, or planning presets without weakening core contracts|
|`tooling.md` | When you need to run route preview, capture continuity, router checker, or find artifact paths|
|`personalization.md` | When editing response-style preferences, adaptive language, or adapter wrappers for customization|
|`release-readiness.md` | When changing the release verdict, rollout tiers, or post-release follow-up contract|
|`adoption-check.md` | When changing the post-deploy signal contract or the handoff back into release-readiness|
|`workspace-init.md` | When editing the skeleton workspace, init flow, or onboarding wrapper while preserving the repo-neutral contract|
|`help-next.md` | When editing navigator logic for help/next, repo-state priority, or operator guidance wrappers|
|`execution-delivery.md` | When editing build packet state, chain checkpoints, browser QA markers, or packet completion state|
|`dashboard.md` | When adding or adjusting the thin dashboard view over packet state, release state, or next-action summaries|
|`run-guidance.md` | When editing workflow `run`, ready-signal detection, command classification, or adapter wrappers for execute-then-route|
|`error-translation.md` | When fixing database error patterns, sanitation rules, or how `run/debug/test` converts technical errors into readable guidance|
|`bump-release.md` | When editing version-bump checklist, semver math, or release artifact update flow|
|`rollback-guidance.md` | When editing rollback planning, risk framing, or recovery strategy selection|
|`canary-rollout.md` | Use when rolling Forge out on a real workspace and confirming readiness with canary artifacts|
|`companion-skill-contract.md` | Design or update companion skills when the repo really has an extended runtime/framework layer|
|`companion-routing-smoke-tests.md` | Check routing between Forge and companion skills when the workspace uses a companion/local layer|

## Reading Order

### When maintaining Forge core

```text
1. SKILL.md
2. architecture-layers.md before moving ownership between core, generated artifacts, workflow state, and runtime tools
3. extension-presets.md when adding bounded packet template, workflow overlay, or planning preset contracts
4. target-state.md if the change affects Forge strategy, process weight, verification strictness, or core identity
5. tooling.md if you need deterministic preview/check instead of reading plain prose
6. personalization.md if you are editing response style or preference engine
7. workspace-init.md if editing init/onboarding skeleton logic
8. help-next.md if editing navigator help/next
9. run-guidance.md if editing run/execute-then-route
10. error-translation.md if you are editing error translator/helper layer
11. bump-release.md or rollback-guidance.md if editing release operators
12. artifact-driven-change-flow.md if validating the medium/risky implementation path end-to-end
13. backend-briefs.md or execution-delivery.md depending on the layer being edited
14. smoke-tests.md / smoke-test-checklist.md if needed to verify host behavior
15. canary-rollout.md if preparing a real rollout
16. companion-skill-contract.md only when editing the companion/runtime layer
17. companion-routing-smoke-tests.md only when testing the companion/runtime layer
```

### When the repo does not have local skills

```text
1. SKILL.md
2. plan.md / architect.md / build.md / debug.md / review.md depending on intent
3. backend-briefs.md or ui-briefs.md if the task needs the first artifact
4. execution-delivery.md or quality-gate.md if the task is long or risky
```

### When you just want to smoke test Forge core

```text
1. smoke-tests.md
2. smoke-test-checklist.md
3. canary-rollout.md if this smoke is part of the actual rollout
```

### When debugging companion routing

```text
1. companion-skill-contract.md
2. companion-routing-smoke-tests.md
3. tooling.md if you need to run checker
4. canary-rollout.md if the bug is appearing in the real workspace
```

### When designing a workspace according to the global + local model

```text
1. companion-skill-contract.md
2. tooling.md
3. companion-routing-smoke-tests.md
4. smoke-tests.md if you need to verify host behavior more broadly
5. canary-rollout.md if you are doing a controlled rollout
```

### When doing implementation after plan/design

```text
1. artifact-driven-change-flow.md
2. target-state.md if the change affects Forge process direction or strictness
3. execution-delivery.md
4. build.md when defining or updating the canonical build packet
5. test.md when the proof chain or browser QA evidence changes
6. debug.md when reproduction or root-cause packet changes
7. failure-recovery-playbooks.md if the chain has risk stall/block
8. tooling.md if checkpoint artifact is needed
9. review.md if you need to clear disposition last
10. quality-gate.md if you need to go/no-go clearly before claiming or deploying
```

### When doing release-critical flow

```text
1. secure.md
2. quality-gate.md
3. deploy.md
4. release-readiness.md if you need the explicit rollout verdict or follow-up packet
5. adoption-check.md if the slice is already live and you need the post-deploy signal
6. failure-recovery-playbooks.md if gate is blocked or rollout fails
7. execution-delivery.md if the chain is long or high-risk
```

### When working on backend tasks

```text
1. backend-briefs.md
2. tooling.md if you want to generate/check/persist backend brief
3. backend.md
4. failure-recovery-playbooks.md if task is migration/recovery/high-risk
5. execution-delivery.md if the backend task spans multiple checkpoints
6. companion-skill-contract.md if the runtime/framework is clear and you want to add more layers
```

### When doing frontend or visualization

```text
1. ui-briefs.md
2. frontend-stack-profiles.md
3. ui-quality-checklist.md
4. ui-good-bad-examples.md
5. ui-heuristics.md
6. ui-escalation.md if the visual guide is too open
7. ui-progress.md if the task takes a long time
8. tooling.md if you want to generate/check/track/persist with script
```

### When stalled or blocked

```text
1. failure-recovery-playbooks.md
2. execution-delivery.md if you need to look back at the chain/checkpoint
3. tooling.md if you need to capture new artifacts
4. debug.md / quality-gate.md / review.md / deploy.md depending on where you're stuck
5. canary-rollout.md if stuck in real rollout phase
```
