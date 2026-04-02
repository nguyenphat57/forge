---
name: forge-core
description: "Forge Core - host-neutral orchestrator source-of-truth for intent routing, complexity assessment, skill composition, delivery guardrails, and optional companion runtime/framework integration across planning, building, debugging, reviewing, designing, testing, deploying, and session work."
---

# Forge Core - Host-Neutral Execution Kernel

> Forge = delivery discipline + skill composition + evidence before claims.
> Forge must be strong and disciplined enough even if the repo does not have any companion skills or local skills.
> Forge is flexible on small tasks and disciplined on medium and large tasks.
> Forge core is the process-first execution kernel for real repos; adapters and companions extend it, but they do not replace its verification or workflow-state contracts.

---

## Bundle Layout

The tree below reflects the current source layout of the core bundle.
For the most up-to-date inventory of scripts, tests, references, and data files, use the package directories and the `Executable Tooling` section below.

- `SKILL.md`: entry point for intent routing, skill composition, and delivery guardrails
- `workflows/design/`: planning, architecture, spec-review, visualization
- `workflows/execution/`: build, debug, test, review, review-pack, change, verify-change, refactor, secure, deploy, release-doc-sync, release-readiness, adoption-check, session
- `workflows/operator/`: help, next, and host-neutral operator workflows
- `domains/`: core domain guidance for frontend and backend
- `data/`: machine-readable registry for intent, matrix, verification profiles, quality profiles, execution pipelines, lane model policy, and personalization schema
- `scripts/`: deterministic tooling for route preview, scoped continuity capture, and optional checks for workspaces with local layers
- `tests/`: regression tests for deterministic scripts and router/tooling contracts
- `references/`: smoke tests, companion contract, and read-only reference documentation when needed
- host metadata files live in adapter bundles, not in the core

```text
forge-core/
├── SKILL.md
├── data/
│ ├── orchestrator-registry.json
│ └── preferences-schema.json
├── domains/
│ ├── backend.md
│ └── frontend.md
├── references/
│ ├── backend-briefs.md
│ ├── bump-release.md
│ ├── canary-rollout.md
│ ├── companion-routing-smoke-tests.md
│ ├── companion-skill-contract.md
│ ├── error-translation.md
│ ├── execution-delivery.md
│ ├── failure-recovery-playbooks.md
│ ├── frontend-stack-profiles.md
│ ├── help-next.md
│ ├── personalization.md
│ ├── reference-map.md
│ ├── rollback-guidance.md
│ ├── run-guidance.md
│ ├── smoke-test-checklist.md
│ ├── smoke-tests.md
│ ├── tooling.md
│ ├── ui-briefs.md
│ ├── ui-escalation.md
│ ├── ui-good-bad-examples.md
│ ├── ui-heuristics.md
│ ├── ui-progress.md
│ ├── ui-quality-checklist.md
│ └── workspace-init.md
├── scripts/
│ ├── capture_continuity.py
│ ├── check_backend_brief.py
│ ├── check_ui_brief.py
│ ├── check_workspace_router.py
│ ├── common.py
│ ├── evaluate_canary_readiness.py
│ ├── generate_backend_brief.py
│ ├── generate_ui_brief.py
│ ├── initialize_workspace.py
│ ├── prepare_bump.py
│ ├── record_canary_result.py
│ ├── resolve_help_next.py
│ ├── resolve_preferences.py
│ ├── resolve_rollback.py
│ ├── route_preview.py
│ ├── run_smoke_matrix.py
│ ├── run_with_guidance.py
│ ├── run_workspace_canary.py
│ ├── track_chain_status.py
│ ├── track_execution_progress.py
│ ├── track_ui_progress.py
│ ├── translate_error.py
│ ├── verify_bundle.py
│ └── write_preferences.py
├── tests/
│ ├── fixtures/
│ ├── support.py
│ ├── test_bump_workflow.py
│ ├── test_canary_rollout.py
│ ├── test_check_workspace_router.py
│ ├── test_contracts.py
│ ├── test_error_translation.py
│ ├── test_help_next.py
│ ├── test_initialize_workspace.py
│ ├── test_preferences.py
│ ├── test_rollback_guidance.py
│ ├── test_router_matrix.py
│ ├── test_route_matrix.py
│ ├── test_route_preview.py
│ ├── test_run_workflow.py
│ ├── test_tool_roundtrip.py
│ ├── test_workspace_canary.py
│ └── test_write_preferences.py
└── workflows/
    ├── design/
    │ ├── architect.md
    │ ├── brainstorm.md
    │ ├── plan.md
    │ ├── spec-review.md
    │ └── visualize.md
    ├── execution/
        ├── build.md
        ├── debug.md
        ├── deploy.md
        ├── quality-gate.md
        ├── refactor.md
        ├── review.md
        ├── secure.md
        ├── session.md
        └── test.md
    └── operator/
        ├── bump.md
        ├── help.md
        ├── next.md
        ├── rollback.md
        └── run.md
```

## Host Boundary

- Forge core is not locked to a specific host.
- Each host's rules live in the corresponding adapter bundle.
- Files like `GEMINI.md`, `AGENTS.md`, UI metadata, or host-level shortcuts are adapter concerns, not core canonical sources.
- Forge core can read workspace router/local skill docs when the host provides them, but the route/verify logic must not depend on a single host rule file.

## Independence Rule

- Forge is **global-first orchestrator**.
- New repos, small repos, or repos without local skills still have to use Forge normally using the workflows/domain skills of this bundle.
- Companion skills and workspace routers are **optional augmentation**, not default dependencies.
- If there is no clear companion or local skill, Forge must still proceed with the core bundle instead of waiting for a fuller setup.

---

## Executable Tooling

- Canonical machine-readable source: `data/orchestrator-registry.json`
- Preferences resolver: `scripts/resolve_preferences.py` (adapter-global Forge preferences -> canonical response-style contract, with optional legacy workspace fallback)
- Preferences writer: `scripts/write_preferences.py` (canonical schema persistence for adapter-level customized flows)
- Workspace init skeleton: `scripts/initialize_workspace.py` (repo-neutral workspace bootstrap for adapter-level init flows)
- Help/next navigator: `scripts/resolve_help_next.py` (repo state -> current focus, suggested workflow, next action)
- Run resolver: `scripts/run_with_guidance.py` (execute command guidance -> classify signal -> route to test/debug/deploy)
- Error translator: `scripts/translate_error.py` (raw stderr/error text -> sanitized human summary + suggested action)
- Bump preparation: `scripts/prepare_bump.py` (explicit semver bump -> update VERSION/CHANGELOG checklist)
- Rollback planner: `scripts/resolve_rollback.py` (scope/risk -> safest recovery strategy + verification)
- Deterministic route preview: `scripts/route_preview.py` (intent + chain + execution pipeline + lane model tiers)
- Workspace router drift check: `scripts/check_workspace_router.py` (only used when the workspace actually has a local routing layer)
- Scoped continuous capture for durable decisions/learnings: `scripts/capture_continuity.py`
- Backend brief generator for medium/large backend work: `scripts/generate_backend_brief.py`
- Backend brief checker for persisted backend artifacts: `scripts/check_backend_brief.py`
- Chain status tracker for long-running multi-skill flows: `scripts/track_chain_status.py` (stages + lanes + model tiers + review loop state)
- Execution progress tracker for long-running build work: `scripts/track_execution_progress.py` (checkpoint + lane + proof-before-progress)
- UI brief generator for frontend/visualize work: `scripts/generate_ui_brief.py`
- UI brief checker for persisted frontend/visualize artifacts: `scripts/check_ui_brief.py`
- UI progress tracker for long-running frontend/visualize tasks: `scripts/track_ui_progress.py`
- Automated smoke matrix runner for route/router cases: `scripts/run_smoke_matrix.py`
- Canonical release/CI verification entry point: `scripts/verify_bundle.py`
- Automated workspace canary runner for real repo rollout: `scripts/run_workspace_canary.py`
- Canary result recorder for real workspace rollout: `scripts/record_canary_result.py`
- Canary readiness evaluator for rollout verdicts: `scripts/evaluate_canary_readiness.py`
- Persisted artifacts default:
  - `.forge-artifacts/route-previews/`
  - `.forge-artifacts/router-checks/`
- `.forge-artifacts/backend-briefs/`
- `.forge-artifacts/chain-status/`
- `.forge-artifacts/execution-progress/`
- `.forge-artifacts/ui-briefs/`
- `<adapter-state-root>/state/preferences.json`
- `<adapter-state-root>/state/extra_preferences.json`
- `.brain/decisions.json`
- `.brain/learnings.json`

When you need detailed command examples or artifact behavior, read `references/tooling.md`.

---

## Response Personalization

- Forge resolves preferences through `scripts/resolve_preferences.py` from adapter-global split state: canonical fields in `state/preferences.json`, adapter extras in `state/extra_preferences.json`, and falls back to `.brain/preferences.json` only for legacy workspaces that have not migrated yet.
- Core schema includes `technical_level`, `detail_level`, `autonomy_level`, `pace`, `feedback_style`, and `personality`.
- The adapter can persist preferences via `scripts/write_preferences.py`, but cannot change key names or validation rules.
- Adapters can add UX wrappers like `customize`, but cannot fork the schema or change the meaning of the response-style contract.

---

## Operator Guidance

- `help` and `next` live in `workflows/operator/` and share the same navigator `scripts/resolve_help_next.py`.
- Repo-first is a hard rule: `git status`, plans/specs, then `.brain`.
- Adapters can add slash aliases or natural-language wrappers, but cannot change the stage model or repo-first contract.
- `run` lives in `workflows/operator/` and uses `scripts/run_with_guidance.py` to turn real output into clear next workflow.
- Error translation is a core helper shared by `run`, `build`, `debug`, and `test`. Raw errors must be sanitized before they are summarized.
- `bump` and `rollback` live in `workflows/operator/` and should activate only when the user explicitly asks for release work.
- The adapter can add `/init` or slim onboarding, but the reusable skeleton workspace must go through `scripts/initialize_workspace.py`.
- Adapters can add a `/run` wrapper or natural-language entry point, but cannot change the meaning of `state`, `command_kind`, or `suggested_workflow`.

---

## Intent Detection

When receiving a prompt from the user, classify the intent:

|Intent | Trigger keywords | For example|
|--------|------------------|-------|
|**BUILD** | add, create, implement, feature, code | "Add payment feature"|
|**DEBUG** | error, bug, fix, fix, error, crash | "Fix the login failure"|
|**OPTIMIZE** | refactor, optimize, clean, tidy up | "Refactor file is too long"|
|**DEPLOY** | deploy, release, production, rollout | "Deploy to Vercel"|
|**REVIEW** | review, evaluate, check, audit | "Review code before merging"|
|**VISUALIZE** | ui, ux, mockup, wireframe, screen, layout | "Checkout screen sketch"|
|**SESSION** | recap, continue, resume, save, context | "Continue unfinished business"|

**When user uses `/shortcut`:** Map according to the action surface of the host adapter, regardless of the local files in this core folder.
Canonical source for intent keywords and chains: `data/orchestrator-registry.json`.

Signals like `brainstorm`, locale-specific brainstorming phrases in active routing locales, `options`, `approach`, and `tradeoff` do not create new intents. They activate the **brainstorm gate** before `plan` when the task is vague or complex enough.

---

## Complexity Assessment

|Level | Criteria | For example|
|-------|----------|-------|
|**small** | <=2 files, small blast radius, clear requirements | Fix typo, edit CSS, change 1 field|
|**medium** | 3-10 files, with behavioral changes or need for assumption | Add filter, CRUD endpoint|
|**large** | >10 new files or features/modules, wide data flow | Payment, auth flow, new modules|

If you are unsure whether the task is small or medium, default to **medium**.
Canonical source for hints and thresholds: `data/orchestrator-registry.json`.

---

## Skill Composition Matrix

Intent + Complexity -> skills can load:

|Intent | small | medium | large|
|--------|-------|--------|-------|
|**BUILD** | `build` | `plan` -> `build` -> `test` -> `quality-gate` | `plan` -> `architect` -> `spec-review` -> `build` -> `test` -> `quality-gate`|
|**DEBUG** | `debug` | `debug` -> `test` | `debug` -> `plan` -> `build` -> `test`|
|**OPTIMIZE** | `refactor` | `refactor` -> `test` | `review` -> `refactor` -> `test`|
|**DEPLOY** | `deploy` | `secure` -> `quality-gate` -> `deploy` | `secure` -> `test` -> `quality-gate` -> `deploy`|
|**REVIEW** | `review` | `review` -> `secure` | `review` -> `secure`|
|**VISUALIZE** | `visualize` | `plan` -> `visualize` | `plan` -> `architect` -> `visualize`|
|**SESSION** | `session` | `session` | `session`|

**Ambiguity gate:** for medium/large `BUILD` or `VISUALIZE`, if the prompt is ambiguous or balances multiple solutions, insert `brainstorm` before `plan`. `Brainstorm` must do more than list options: it should lock a recommendation that `plan` can inherit, or clearly record the unresolved decision.
**Spec-review gate:** for `BUILD large`, or for `BUILD medium` that touches contracts, schema, migration, auth, payment, public interfaces, or another high-risk boundary, insert `spec-review` before `build`.
**Execution pipeline gate:** for large `BUILD/DEBUG/OPTIMIZE`, or for profiles stronger than `standard`, add an independent reviewer lane by default. When `BUILD` already includes `spec-review`, prefer the `implementer -> spec-reviewer -> quality-reviewer` pipeline.
**Lane model policy:** use abstract tier `cheap / standard / capable` according to lane instead of pushing every step to the same capacity level.

**Domain skills** (`frontend`, `backend`) added when the task involves UI or API/database/service layer.
**Companion runtime/language skills** (Python, Java, Go, .NET, framework-specific) are optional augmentations when the repo/framework is already known. Forge should still run well without them.
Companion skill contract: see `references/companion-skill-contract.md` when you are actually adding a runtime/framework layer.
If the workspace has `AGENTS.md` or a router doc that points to local skills, use that router as the source of truth for this extension layer. If not, Forge should continue with its own bundle.
To preview routing deterministically for a specific prompt, run `scripts/route_preview.py`.

### How to load skills

```
1. Detect intent + complexity
2. Look up matrix -> list of Forge skills needed
3. Choose execution pipeline and lane model tiers if the task is large/risky enough
4. Choose enough Forge chain to solve the task with this bundle
5. Check repo signals (`package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`,...)
6. If you have a suitable companion skill that really helps increase accuracy -> add it to the chain
7. If the workspace has a router doc for local skills -> use it as an extended layer, do not replace Forge
8. User notification: "Forge: [intent] | [complexity] | Skills: [list]"
9. Load skill first
10. Complete important quality gate
11. Just move on to the next skill if needed
```

You do not need to load the full chain if the task is already resolved safely.
Companion and local skills cannot override Forge's verification/evidence gate.

**Minimal routing policy:** For `REVIEW`, `SESSION`, and task `small`, Forge prioritizes prompt-led routing. Repo signals at this time will not automatically pull additional domain skills, local companions, or escalation profiles if the prompt does not clearly state the need.

---

## Verification Strategy

Applies to all intents with modifications:

- **Behavioral code change + with harness** -> prioritize failing test or reproduction before editing.
- **Behavioral code change + no viable harness** -> create clear manual reproduction, failing command, or smoke scenario before editing.
- **Non-behavioral change** (`docs`, `config`, `build script`, `release chores`) -> close verification command before editing: build, lint, typecheck, diff, or smoke run.

Do not fake TDD if the project does not have a harness. Do not skip verification if the harness is not available.
Verification profiles canonical live in `data/orchestrator-registry.json`.

## Execution Upgrade Notes

- Forge uses `execution pipeline` to avoid implementing and reviewing in the same lane.
- Forge uses `lane model tiers` to optimize cost: navigation/triage can be cheaper than spec-review or release gates.
- Forge uses `quality-gate` as canonical source for evidence response contract and anti-rationalization.
- Forge keeps **proof before claims** as the non-negotiable handoff contract across every lane and host.
- Forge uses build packets for medium/large execution; `track_execution_progress.py` is the packet source of truth and summaries are read models.
- Dispatch language should stay compatible across `parallel-split`, `independent-reviewer`, and `controller-sequential`; host capability changes dispatch mode, not packet semantics.
- The `spec-review` loop allows at most `3` revision rounds for the same packet. Beyond that threshold, the status must become `blocked`.
- Continuity stays bounded through a packet index read model; it speeds reads but does not replace workflow-state.
- Extension and preset surfaces are bounded overlays only; they cannot override core packet, verification, or workflow-state contracts.

## Solo Profile And Workflow-State Contract

- `solo-internal` and `solo-public` are profile overlays for a single operator, not separate orchestration systems.
- `brainstorm` should begin with `discovery-lite` and only escalate to `discovery-full` when the first pass still leaves scope or boundary risk unclear.
- `spec-review` is a risk gate, not a size gate: if the packet is ambiguous, contract-boundary heavy, or release-sensitive, review it before build even when the task sounds small.
- `review` becomes `self-review` for solo-dev flows, but the findings-first bar does not relax.
- `review-pack` is the pre-release tail for release-sensitive work and should feed `self-review`, then `quality-gate`, then `deploy`.
- Release-tail stages stay explicit: `review-pack` -> `self-review` -> `quality-gate` -> `release-doc-sync` -> `release-readiness` -> `deploy` -> `adoption-check`.
- `release-doc-sync`, `release-readiness`, and `adoption-check` are release-surface gates that must remain visible when the slice affects docs, rollout confidence, or post-deploy usage.
- Release-tier language should stay compatible with the core release contract; adapters may present host-specific wording, but they must not invent separate posture names that change the behavior bar.
- workflow-state records should use the canonical stage status vocabulary: `pending`, `required`, `active`, `completed`, `skipped`, `blocked`.
- workflow-state entries should carry activation reasons and skip reasons so the gate does not have to reconstruct intent from chat memory.

---

## Skill Registry

|Skill | File | Type | Iron Law|
|------|------|------|----------|
|brainstorm | `workflows/design/brainstorm.md` | flexible | NO AMBIGUOUS MEDIUM/LARGE WORK WITHOUT CHOOSING A DIRECTION FIRST|
|plan | `workflows/design/plan.md` | flexible | NO MEDIUM/LARGE BUILD WITHOUT A CONFIRMED PLAN|
|architect | `workflows/design/architect.md` | flexible | NO LARGE IMPLEMENTATION WITHOUT ARCHITECTURE DECISIONS DOCUMENTED|
|spec-review | `workflows/design/spec-review.md` | rigid | NO HIGH-RISK BUILD WITHOUT A BUILD-READINESS REVIEW FIRST|
|build | `workflows/execution/build.md` | rigid | NO BEHAVIORAL CHANGE WITHOUT DEFINING VERIFICATION FIRST|
|frontend | `domains/frontend.md` | flexible | PRESERVE THE EXISTING DESIGN SYSTEM BEFORE INVENTING A NEW ONE|
|backend | `domains/backend.md` | flexible | VALIDATE AT THE BOUNDARY, KEEP LOGIC OUT OF TRANSPORT|
|debug | `workflows/execution/debug.md` | rigid | NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION|
|test | `workflows/execution/test.md` | rigid | USE FAILING TESTS FIRST WHEN A HARNESS EXISTS|
|secure | `workflows/execution/secure.md` | rigid | NO RELEASE WITHOUT EXPLICIT SECURITY REVIEW|
|deploy | `workflows/execution/deploy.md` | rigid | NO DEPLOY WITHOUT VERIFIED QUALITY GATES|
|quality-gate | `workflows/execution/quality-gate.md` | rigid | NO CLAIMS, HANDOFFS, OR DEPLOYS WITHOUT A FRESH GO / NO-GO DECISION|
|review | `workflows/execution/review.md` | flexible | FINDINGS FIRST, SUMMARY SECOND|
|refactor | `workflows/execution/refactor.md` | rigid | NO REFACTOR WITHOUT BASELINE AND AFTER VERIFICATION|
|visualize | `workflows/design/visualize.md` | flexible | DO NOT CODE UI BEFORE THE INTERACTION MODEL IS CLEAR|
|session | `workflows/execution/session.md` | flexible | REBUILD CONTEXT FROM REAL ARTIFACTS BEFORE WRITING MEMORY|
|help | `workflows/operator/help.md` | flexible | REPO-FIRST GUIDANCE, NOT RECAP THEATER|
|next | `workflows/operator/next.md` | flexible | ONE CONCRETE NEXT STEP, NOT VAGUE MOMENTUM TALK|
|run | `workflows/operator/run.md` | flexible | EXECUTE THE REAL COMMAND, THEN ROUTE FROM EVIDENCE|
|bump | `workflows/operator/bump.md` | flexible | VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION|
|rollback | `workflows/operator/rollback.md` | flexible | DO NOT BLINDLY ROLL BACK WITHOUT SCOPE, RISK, AND POST-ROLLBACK VERIFICATION|

**Rigid skills:** do not ignore evidence and quality gate.
**Flexible skills:** adapt according to context, but still have to be clear about output and next step.

---

## Global Resilience

### Auto-Retry
```
Network error, timeout, file write:
1. Retry once
2. Retry a second time if the error seems temporary
3. If it still fails -> notify user + propose a fallback
```

### Long-Running Work
```
If the task takes too long or the command repeatedly fails:
1. Tell the user where the work is stuck
2. Summarize what has been tried
3. Propose the safest next step
```

### Error Translation (when needed)

|Original error | Translation|
|---------|------|
|`ECONNREFUSED` | The service or database is not enabled|
|`Cannot read undefined` | Reading data that does not exist yet|
|`Module not found` | Missing package or wrong import path|
|`CORS error` | The server is blocking requests from this origin|
|`401 Unauthorized` | Not logged in or token expired|
|`Hydration mismatch` | HTML server and client render differently|

---

## Golden Rules

```
1. DO ONLY WHAT WAS REQUESTED - Do not expand scope on your own
2. ONE THING AT A TIME - Finish A before jumping to B
3. MINIMAL CHANGE - Edit exactly what needs to change
4. ASK BEFORE BIG CHANGES - Schema, folder structure, new dependency -> ask first
5. EVIDENCE BEFORE CLAIMS - Verify before saying "done"
```

## Reference Map

Quick entry point for references: see `references/reference-map.md`.

## Activation Announcement

```
Forge Core: orchestrator | route the right intent, keep evidence before claims
```
