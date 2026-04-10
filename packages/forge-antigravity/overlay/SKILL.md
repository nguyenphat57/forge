---
name: forge-antigravity
description: "Forge Antigravity - skill-oriented orchestrator optimized for Antigravity workspaces. Use when a request needs intent routing, complexity assessment, skill composition, Antigravity-friendly session handling, shared delivery guardrails, and optional companion runtime/language skill integration across planning, building, debugging, reviewing, designing, testing, deploying, or session restore/save work."
---

# Forge Antigravity - Core Orchestrator

> Forge = delivery discipline + skill composition + evidence before claims.
> Forge must be strong and disciplined enough even if the repo does not have any companion skills or local skills.
> Forge is flexible on small tasks and disciplined on medium and large tasks.
> Forge Antigravity maps the Forge process-first execution kernel onto Gemini workspaces through `GEMINI.md`, Antigravity-native operator wrappers, and the same shared verification contract as core.

---

## Bundle Layout

The tree below reflects the Antigravity bundle after overlaying this adapter on top of `forge-core`.
Core files and adapter files appear together in a single runtime layout.

- `SKILL.md`: entrypoint to route intent, pair skills, and hold delivery guardrails
- `workflows/design/`: planning, architecture, spec-review, and visualize
- `workflows/execution/`: build, debug, test, review, refactor, secure, deploy, session
- `workflows/operator/`: help, next, run, bump, rollback, primary wrappers such as customize/init, and compatibility wrappers for recap/save-brain/handover
- `domains/`: core domain guidance for frontend and backend
- `data/`: machine-readable registry for intent, matrix, verification profiles, quality profiles, execution pipelines, and lane model policy
- `scripts/`: deterministic tooling for route preview, scoped continuity capture, and optional checks for workspaces with local layers
- `tests/`: regression tests for deterministic scripts and routing/tooling contracts
- `references/`: smoke tests, the companion contract, and read-only reference documentation when needed
- `agents/openai.yaml`: UI metadata for hosts that support skill list/chips

```text
forge-antigravity/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── data/
│   ├── orchestrator-registry.json
│   ├── output-contracts.json
│   ├── preferences-compat.json
│   ├── preferences-schema.json
│   ├── routing-locales.json
│   └── routing-locales/
│       └── vi.json
├── domains/
│   ├── backend.md
│   └── frontend.md
├── references/
│   ├── antigravity-operator-surface.md
│   ├── backend-briefs.md
│   ├── bump-release.md
│   ├── canary-rollout.md
│   ├── companion-routing-smoke-tests.md
│   ├── companion-skill-contract.md
│   ├── error-translation.md
│   ├── execution-delivery.md
│   ├── failure-recovery-playbooks.md
│   ├── frontend-stack-profiles.md
│   ├── help-next.md
│   ├── personalization.md
│   ├── reference-map.md
│   ├── rollback-guidance.md
│   ├── run-guidance.md
│   ├── smoke-test-checklist.md
│   ├── smoke-tests.md
│   ├── tooling.md
│   ├── ui-briefs.md
│   ├── ui-escalation.md
│   ├── ui-good-bad-examples.md
│   ├── ui-heuristics.md
│   ├── ui-progress.md
│   ├── ui-quality-checklist.md
│   └── workspace-init.md
├── scripts/
│   ├── capture_continuity.py
│   ├── check_backend_brief.py
│   ├── check_ui_brief.py
│   ├── check_workspace_router.py
│   ├── common.py
│   ├── compat.py
│   ├── error_translation.py
│   ├── evaluate_canary_readiness.py
│   ├── generate_backend_brief.py
│   ├── generate_ui_brief.py
│   ├── initialize_workspace.py
│   ├── preferences.py
│   ├── prepare_bump.py
│   ├── record_canary_result.py
│   ├── resolve_help_next.py
│   ├── resolve_preferences.py
│   ├── resolve_rollback.py
│   ├── route_preview.py
│   ├── run_smoke_matrix.py
│   ├── run_with_guidance.py
│   ├── run_workspace_canary.py
│   ├── skill_routing.py
│   ├── style_maps.py
│   ├── text_utils.py
│   ├── track_chain_status.py
│   ├── track_execution_progress.py
│   ├── track_ui_progress.py
│   ├── translate_error.py
│   ├── verify_bundle.py
│   └── write_preferences.py
├── tests/
│   ├── fixtures/
│   ├── support.py
│   ├── test_adapter_locales.py
│   ├── test_bump_workflow.py
│   ├── test_canary_rollout.py
│   ├── test_check_workspace_router.py
│   ├── test_contracts.py
│   ├── test_error_translation.py
│   ├── test_help_next.py
│   ├── test_initialize_workspace.py
│   ├── test_preferences.py
│   ├── test_rollback_guidance.py
│   ├── test_router_matrix.py
│   ├── test_route_matrix.py
│   ├── test_route_preview.py
│   ├── test_run_workflow.py
│   ├── test_tool_roundtrip.py
│   ├── test_workspace_canary.py
│   └── test_write_preferences.py
└── workflows/
    ├── design/
    │   ├── architect.md
    │   ├── brainstorm.md
    │   ├── plan.md
    │   ├── spec-review.md
    │   └── visualize.md
    ├── execution/
    │   ├── build.md
    │   ├── debug.md
    │   ├── deploy.md
    │   ├── quality-gate.md
    │   ├── refactor.md
    │   ├── review.md
    │   ├── secure.md
    │   ├── session.md
    │   └── test.md
    └── operator/
        ├── bump.md
        ├── customize.md
        ├── handover.md
        ├── help.md
        ├── init.md
        ├── next.md
        ├── recap.md
        ├── rollback.md
        ├── run.md
        └── save-brain.md
```

## Host Boundary

- Antigravity host rules live above this folder.
- The root `GEMINI.md` at Antigravity scope, when the host uses it, is a **host rule file** and not part of this skill bundle.
- `AGENTS.md` at the workspace root is a **router/instruction file** for the workspace, not `SKILL.md`.
- `forge-antigravity` can use host or workspace rules when present, but it does not depend on a local `GEMINI.md` inside this folder.

## Antigravity Protocol Bridge

Forge concepts map directly to Antigravity host tools. Use native Antigravity tools instead of duplicating ceremony.

| Forge concept | Antigravity tool | Mapping |
|--------------|-----------------|--------|
| Activation line | `task_boundary` | `TaskName` = Forge skill name, `Mode` = PLANNING/EXECUTION/VERIFICATION |
| Skill chain progress | `task_boundary` | Update `TaskStatus` as you move through the chain |
| Intent + complexity | `task_boundary` | Include in first `TaskSummary`: `"Forge: BUILD \| medium"` |
| Evidence reporting | `notify_user` | Use `PathsToReview` for plans/walkthroughs needing approval |
| Blocked on user | `notify_user` | Set `BlockedOnUser=true` when spec/plan needs explicit approval |

Mode mapping from Forge skills:

| Forge skill phase | Antigravity Mode |
|------------------|------------------|
| `brainstorm`, `plan`, `architect`, `spec-review` | `PLANNING` |
| `build`, `debug`, `refactor`, `deploy`, `secure` | `EXECUTION` |
| `test`, `review`, `quality-gate` | `VERIFICATION` |
| `session`, `visualize` | Use the mode that matches current activity |

Rules:
- Do **not** emit a separate Forge activation line and a `task_boundary` call; the `task_boundary` call is the activation.
- Forge skill chain progress updates go through `task_boundary(TaskStatus)`, not through inline messages.
- When Forge completes a skill and moves to the next in the chain, update `TaskName` to reflect the new skill.
- Evidence and verification results that need user review go through `notify_user`, not inline.

## Antigravity Artifact Boundary

Two artifact paths serve different scopes:

| Path | Scope | Purpose | Examples |
|------|-------|---------|----------|
| `.forge-artifacts/` | Workspace-scoped, durable across conversations | Forge tooling output: route previews, briefs, chain status, execution progress | `route-previews/`, `backend-briefs/`, `ui-briefs/` |
| `brain/<conversation>/` | Conversation-scoped, managed by Antigravity host | Host artifacts: task.md, implementation_plan.md, walkthrough.md | `task.md`, `walkthrough.md` |

Rules:
- Forge deterministic scripts persist to `.forge-artifacts/` by default.
- Antigravity host artifacts (`task_boundary` artifacts) persist to `brain/<conversation>/`.
- Do **not** mix paths: Forge script output stays in `.forge-artifacts/`, host artifacts stay in `brain/`.
- `.brain/decisions.json` and `.brain/learnings.json` are workspace memory and belong to the workspace `.brain/` layer.

## Independence Rule

- Forge is a **global-first orchestrator**.
- New repos, small repos, or repos without local skills must still use Forge normally through the workflows/domain skills of this bundle.
- Companion skills and workspace routers are **optional augmentation**, not default dependencies.
- If there is no clear companion/local skill, Forge must not hesitate or wait for a "full skill set" before working.

---

## Executable Tooling

- Canonical machine-readable source: `data/orchestrator-registry.json`
- Preferences resolver: `scripts/resolve_preferences.py` (adapter-global Forge preferences -> canonical response-style contract, with optional legacy workspace fallback)
- Preferences writer: `scripts/write_preferences.py` (canonical schema persistence for `/customize`)
- Workspace init skeleton: `scripts/initialize_workspace.py` (repo-neutral bootstrap for `/init`)
- Help/next navigator: `scripts/resolve_help_next.py` (repo state -> current focus, suggested workflow, next action)
- Run guidance resolver: `scripts/run_with_guidance.py` (execute command -> classify signal -> route to test/debug/deploy)
- Error translator: `scripts/translate_error.py` (raw stderr/error text -> sanitized human summary + suggested action)
- Bump preparation: `scripts/prepare_bump.py` (explicit or inferred semver bump -> update VERSION/CHANGELOG checklist)
- Rollback planner: `scripts/resolve_rollback.py` (scope/risk -> safest recovery strategy + verification)
- Deterministic route preview: `scripts/route_preview.py` (intent + chain + execution pipeline + lane model tiers)
- Workspace router drift check: `scripts/check_workspace_router.py` (only used when the workspace actually has a local routing layer)
- Scoped continuity capture for durable decisions/learnings: `scripts/capture_continuity.py`
- Backend brief generator for medium/large backend work: `scripts/generate_backend_brief.py`
- Backend brief checker for persisted backend artifacts: `scripts/check_backend_brief.py`
- Chain status tracker for long-running multi-skill flows: `scripts/track_chain_status.py` (stages + lanes + model tiers + review loop state)
- Execution progress tracker for long-running build work: `scripts/track_execution_progress.py` (checkpoint + lane + proof-before-progress)
- UI brief generator for frontend/visualize work: `scripts/generate_ui_brief.py`
- UI brief checker for persisted frontend/visualize artifacts: `scripts/check_ui_brief.py`
- UI progress tracker for long-running frontend/visualize tasks: `scripts/track_ui_progress.py`
- Automated smoke matrix runner for route/router cases: `scripts/run_smoke_matrix.py`
- Canonical release/CI verification entrypoint: `scripts/verify_bundle.py`
- Automated workspace canary runner for real repo rollout: `scripts/run_workspace_canary.py`
- Canary result recorder for real workspace rollout: `scripts/record_canary_result.py`
- Canary readiness evaluator for rollout verdicts: `scripts/evaluate_canary_readiness.py`
- Default persisted artifacts (see `Antigravity Artifact Boundary` for scope rules):
  - `.forge-artifacts/route-previews/` (workspace-scoped)
  - `.forge-artifacts/router-checks/` (workspace-scoped)
  - `.forge-artifacts/backend-briefs/` (workspace-scoped)
  - `.forge-artifacts/chain-status/` (workspace-scoped)
  - `.forge-artifacts/execution-progress/` (workspace-scoped)
  - `.forge-artifacts/ui-briefs/` (workspace-scoped)
  - `~/.gemini/antigravity/forge-antigravity/state/preferences.json` (adapter-global)
  - `~/.gemini/antigravity/forge-antigravity/state/extra_preferences.json` (adapter-global)
  - `.brain/decisions.json` (workspace memory)
  - `.brain/learnings.json` (workspace memory)

For detailed command examples or artifact behavior, read `references/tooling.md`.

---

## Response Personalization

- At the start of each new thread, resolve preferences before the first substantive user-facing reply so Antigravity-global state is restored automatically.
- Forge resolves preferences through the core engine `scripts/resolve_preferences.py` from the Antigravity-global split state: canonical fields in `state/preferences.json`, adapter extras in `state/extra_preferences.json`, and only falls back to `.brain/preferences.json` for workspace legacy.
- Canonical schema includes `technical_level`, `detail_level`, `autonomy_level`, `pace`, `feedback_style`, and `personality`.
- When the state file contains an Antigravity native legacy payload, this adapter only maps that payload to the canonical schema for reading or migration; the steady-state write path remains the split-file canonical + extras from core.
- `forge-antigravity` ships compat defaults so that a clean install resolves `language=vi` and `orthography=vietnamese_diacritics` by default until state or workspace overrides them.
- `forge-antigravity` may add wrappers like `/customize`, but schema and response-style semantics must still be read from core.
- Durable preference updates, including `language` and `orthography`, must go through `scripts/write_preferences.py`; workspace `.brain/preferences.json` is only for per-repo overrides or legacy fallback.
- Host UX may be richer than Codex, but must not fork key names or validation rules.

---

## Operator Guidance

- `forge-antigravity` may expose `/help` and `/next`, but guidance must still resolve from the core navigator `scripts/resolve_help_next.py`.
- Repo-first remains a hard rule: `git status`, plans/specs, then `.brain`.
- Wrapper UX may be more operator-friendly, but must not turn guidance into recap theater.
- `forge-antigravity` may expose `/run`, but results must still resolve from the core `scripts/run_with_guidance.py`.
- Error translation still reads from the core helper `scripts/translate_error.py`; this adapter only changes presentation, not the pattern database.
- `/bump` and `/rollback` may be explicitly exposed in Antigravity, but must still maintain the user-requested/inference-justified and risk-first contract of core.
- `/init` may be richer in onboarding, but the reusable workspace skeleton must still go through `scripts/initialize_workspace.py`.
- Compatibility aliases like `/recap`, `/save-brain`, and `/handover` may stay available during migration, but they are not the primary surface.
- Compatibility wrappers may be richer in UX, but must not change `state`, `command_kind`, or `suggested_workflow` from core, and they must emit deprecation warnings.

---

## Solo Profile And Workflow-State Contract

- `solo-internal` and `solo-public` are profile overlays for a single operator, not separate orchestration systems.
- `review-pack` is the pre-release tail for release-sensitive work and should feed `self-review`, then `quality-gate`, then `deploy`.
- Release-tail stages stay explicit: `review-pack` -> `self-review` -> `quality-gate` -> `release-doc-sync` -> `release-readiness` -> `deploy` -> `adoption-check`.
- `release-doc-sync`, `release-readiness`, and `adoption-check` are release-surface gates that must remain visible when the slice affects docs, rollout confidence, or post-deploy usage.
- Release-tier language should stay compatible with the core release contract; host-specific wording is allowed, but new posture names are not if they change the behavior bar.
- workflow-state records should use the canonical stage status vocabulary: `pending`, `required`, `active`, `completed`, `skipped`, `blocked`.
- workflow-state entries should carry activation reasons and skip reasons so the gate does not have to reconstruct intent from chat memory.
- There is no `/gate` alias; `quality-gate` stays the stage name.

---

## Antigravity Operator Surface

Primary wrappers:

| Surface | Wrapper | Core contract |
|---------|---------|---------------|
| `/help` | `workflows/operator/help.md` | `scripts/resolve_help_next.py --mode help` |
| `/next` | `workflows/operator/next.md` | `scripts/resolve_help_next.py --mode next` |
| `/run` | `workflows/operator/run.md` | `scripts/run_with_guidance.py` |
| `/bump` | `workflows/operator/bump.md` | `scripts/prepare_bump.py` |
| `/rollback` | `workflows/operator/rollback.md` | `scripts/resolve_rollback.py` |
| `/customize` | `workflows/operator/customize.md` | `scripts/resolve_preferences.py` + `scripts/write_preferences.py` |
| `/init` | `workflows/operator/init.md` | `scripts/initialize_workspace.py` |

Compatibility session wrappers:

| Alias | Wrapper | Core contract |
|-------|---------|---------------|
| `/recap` | `workflows/operator/recap.md` | `workflows/execution/session.md` restore mode |
| `/save-brain` | `workflows/operator/save-brain.md` | `workflows/execution/session.md` save mode |
| `/handover` | `workflows/operator/handover.md` | `workflows/execution/session.md` handover mode |

Compatibility rules:

- Aliases exist only to reduce migration friction, not to create new intents.
- Wrapper docs may be more operator-friendly, but deterministic semantics must still be read from core.
- Detailed mapping: `references/antigravity-operator-surface.md`.

---

## Intent Detection

When receiving a prompt from the user, classify the intent:

| Intent | Trigger keywords | Example |
|--------|------------------|---------|
| **BUILD** | add, create, implement, feature, code | "Add payment feature" |
| **DEBUG** | error, bug, fix, crash | "Fix login failure" |
| **OPTIMIZE** | refactor, optimize, clean, tidy | "Refactor overly long file" |
| **DEPLOY** | deploy, release, production, rollout | "Deploy to Vercel" |
| **REVIEW** | review, evaluate, check, audit | "Review code before merge" |
| **VISUALIZE** | ui, ux, mockup, wireframe, screen, layout | "Sketch checkout screen" |
| **SESSION** | continue, resume, save context, handover | "Continue unfinished work" |

**When the user uses `/shortcut`:** Map according to the Antigravity host shortcut registry, not local files in this skill folder.
Canonical source for intent keywords and chains: `data/orchestrator-registry.json`.

Signals like `brainstorm`, `options`, `approach`, and `tradeoff` do not create new intents; they activate the **brainstorm gate** before `plan` when the task is ambiguous or complex enough.

---

## Complexity Assessment

| Level | Criteria | Example |
|-------|----------|---------|
| **small** | <=2 files, small blast radius, clear requirements | Fix typo, edit CSS, change 1 field |
| **medium** | 3-10 files, behavioral change or needs assumption | Add filter, CRUD endpoint |
| **large** | >10 files or new feature/module, wide data flow | Payment, auth flow, new module |

When in doubt between small and medium -> default to **medium**.
Canonical source for hints and thresholds: `data/orchestrator-registry.json`.

---

## Skill Composition Matrix

Intent + Complexity -> skills to load:

| Intent | small | medium | large |
|--------|-------|--------|-------|
| **BUILD** | `build` | `plan` -> `build` -> `test` -> `quality-gate` | `plan` -> `architect` -> `spec-review` -> `build` -> `test` -> `quality-gate` |
| **DEBUG** | `debug` | `debug` -> `test` | `debug` -> `plan` -> `build` -> `test` |
| **OPTIMIZE** | `refactor` | `refactor` -> `test` | `review` -> `refactor` -> `test` |
| **DEPLOY** | `deploy` | `secure` -> `quality-gate` -> `deploy` | `secure` -> `test` -> `quality-gate` -> `deploy` |
| **REVIEW** | `review` | `review` -> `secure` | `review` -> `secure` |
| **VISUALIZE** | `visualize` | `plan` -> `visualize` | `plan` -> `architect` -> `visualize` |
| **SESSION** | `session` | `session` | `session` |

**Ambiguity gate:** For `BUILD` or `VISUALIZE` at medium/large, if the prompt is ambiguous or weighing multiple approaches, insert `brainstorm` before `plan`. `Brainstorm` must not just list options; it must lock a recommendation strong enough for `plan` to inherit, or record exactly one missing decision question.
**Spec-review gate:** For `BUILD large`, or `BUILD medium` touching contract/schema/migration/auth/payment/public interface/high-risk boundary, insert `spec-review` before `build`.
**Execution pipeline gate:** For large `BUILD/DEBUG/OPTIMIZE` or profiles stronger than `standard`, add an independent reviewer lane by default; for `BUILD` with `spec-review`, lean towards the `implementer -> spec-reviewer -> quality-reviewer` pipeline.
**Lane model policy:** Use abstract tiers `cheap / standard / capable` per lane instead of pushing every step to the same capacity level.

**Domain skills** (`frontend`, `backend`) are added when the task involves UI or API/database/service layer.
**Companion runtime/language skills** (Python, Java, Go, .NET, framework-specific) are optional augmentation when the repo/framework is already known. Forge must still work fine without them.
Companion skill contract: see `references/companion-skill-contract.md` when you are actually adding a runtime/framework layer.
If the workspace has `AGENTS.md` or a router doc pointing to local skills, use that router as the source-of-truth for this extension layer; if not, Forge continues with its own bundle.
To preview deterministic routing for a specific prompt: run `scripts/route_preview.py`.

### How to load skills

```
1. Detect intent + complexity
2. Look up matrix -> list of Forge skills needed
3. Choose execution pipeline and lane model tiers if the task is large/risky enough
4. Choose a Forge chain sufficient to solve the task with this bundle
5. Check repo signals (`package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, ...)
6. If a suitable companion skill exists and genuinely increases accuracy -> add it to the chain
7. If the workspace has a router doc for local skills -> use it as an extension layer, do not replace Forge
8. Notify user: "Forge: [intent] | [complexity] | Skills: [list]"
9. Load the first skill
10. Complete the important quality gate
11. Move to the next skill only if needed
```

Do not load the full chain if an earlier step resolves the task safely.
Companion/local skills must not override Forge's verification/evidence gates.

**Minimal routing policy:** For `REVIEW`, `SESSION`, and `small` tasks, Forge prioritizes prompt-led routing. Repo signals must not automatically pull additional domain skills, local companions, or escalation profiles unless the prompt clearly states the need.

---

## Verification Strategy

Applies to all intents with modifications:

- **Behavioral code change + harness available** -> prioritize failing test or reproduction before editing.
- **Behavioral code change + no viable harness** -> create a clear manual reproduction, failing command, or smoke scenario before editing.
- **Non-behavioral change** (`docs`, `config`, `build script`, `release chores`) -> lock the verification command before editing: build, lint, typecheck, diff, or smoke run.

Do not fake TDD if the project has no harness. Do not skip verification if no harness is available.
Verification profiles canonical source: `data/orchestrator-registry.json`.

## Execution Upgrade Notes

- Forge uses `execution pipeline` to avoid implementing and reviewing in the same lane.
- Forge uses `lane model tiers` to optimize cost: navigation/triage can be cheaper than spec-review or release gates.
- Forge uses `quality-gate` as the canonical source for the evidence response contract, the global `Skill selection:` explanation, the global `Skills used:` footer, and anti-rationalization.
- `spec-review` loop is capped at `3` revision rounds for the same packet; beyond this threshold it must be `blocked`.

---

## Skill Registry

| Skill | File | Type | Iron Law |
|-------|------|------|----------|
| brainstorm | `workflows/design/brainstorm.md` | flexible | NO AMBIGUOUS MEDIUM/LARGE WORK WITHOUT CHOOSING A DIRECTION FIRST |
| plan | `workflows/design/plan.md` | flexible | NO MEDIUM/LARGE BUILD WITHOUT A CONFIRMED PLAN |
| architect | `workflows/design/architect.md` | flexible | NO LARGE IMPLEMENTATION WITHOUT ARCHITECTURE DECISIONS DOCUMENTED |
| spec-review | `workflows/design/spec-review.md` | rigid | NO HIGH-RISK BUILD WITHOUT A BUILD-READINESS REVIEW FIRST |
| build | `workflows/execution/build.md` | rigid | NO BEHAVIORAL CHANGE WITHOUT DEFINING VERIFICATION FIRST |
| frontend | `domains/frontend.md` | flexible | PRESERVE THE EXISTING DESIGN SYSTEM BEFORE INVENTING A NEW ONE |
| backend | `domains/backend.md` | flexible | VALIDATE AT THE BOUNDARY, KEEP LOGIC OUT OF TRANSPORT |
| debug | `workflows/execution/debug.md` | rigid | NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION |
| test | `workflows/execution/test.md` | rigid | USE FAILING TESTS FIRST WHEN A HARNESS EXISTS |
| secure | `workflows/execution/secure.md` | rigid | NO RELEASE WITHOUT EXPLICIT SECURITY REVIEW |
| deploy | `workflows/execution/deploy.md` | rigid | NO DEPLOY WITHOUT VERIFIED QUALITY GATES |
| quality-gate | `workflows/execution/quality-gate.md` | rigid | NO CLAIMS, HANDOFFS, OR DEPLOYS WITHOUT A FRESH GO / NO-GO DECISION |
| review | `workflows/execution/review.md` | flexible | FINDINGS FIRST, SUMMARY SECOND |
| refactor | `workflows/execution/refactor.md` | rigid | NO REFACTOR WITHOUT BASELINE AND AFTER VERIFICATION |
| visualize | `workflows/design/visualize.md` | flexible | DO NOT CODE UI BEFORE THE INTERACTION MODEL IS CLEAR |
| session | `workflows/execution/session.md` | flexible | REBUILD CONTEXT FROM REAL ARTIFACTS BEFORE WRITING MEMORY |
| help | `workflows/operator/help.md` | flexible | REPO-FIRST GUIDANCE, NOT RECAP THEATER |
| next | `workflows/operator/next.md` | flexible | ONE CONCRETE NEXT STEP, NOT VAGUE MOMENTUM TALK |
| run | `workflows/operator/run.md` | flexible | EXECUTE THE REAL COMMAND, THEN ROUTE FROM EVIDENCE |
| bump | `workflows/operator/bump.md` | flexible | VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION |
| rollback | `workflows/operator/rollback.md` | flexible | DO NOT BLINDLY ROLL BACK WITHOUT SCOPE, RISK, AND POST-ROLLBACK VERIFICATION |
| customize | `workflows/operator/customize.md` | flexible | DO NOT FORK THE CORE PREFERENCES SCHEMA OR WRITE HOST-LOCAL KEYS |
| init | `workflows/operator/init.md` | flexible | DO NOT OVERWRITE EXISTING REPO FILES DURING BOOTSTRAP |

**Rigid skills:** must not skip evidence and quality gates.
**Flexible skills:** adapt to context, but must still produce clear output and next step.

Compatibility wrappers for `/recap`, `/save-brain`, and `/handover` remain in `workflows/operator/` for one stable line and should only be presented as deprecated migration surfaces.

---

## Global Resilience

### Auto-Retry
```
Network error, timeout, file write:
1. Retry once
2. Retry a second time if the error seems transient
3. Still fails -> notify user + propose fallback
```

### Long-Running Work
```
If the task drags on or a command repeatedly fails:
1. Tell the user where you are stuck
2. Summarize what was already tried
3. Propose the safest next step
```

### Error Translation (when needed)

| Raw error | Translation |
|-----------|-------------|
| `ECONNREFUSED` | Service or database is not running |
| `Cannot read undefined` | Reading data that does not exist yet |
| `Module not found` | Missing package or wrong import path |
| `CORS error` | Server is blocking requests from this origin |
| `401 Unauthorized` | Not logged in or token expired |
| `Hydration mismatch` | Server and client rendered different HTML |

---

## Golden Rules

```
1. DO EXACTLY WHAT IS ASKED - Do not expand scope on your own
2. ONE THING AT A TIME - Finish A before jumping to B
3. MINIMAL CHANGES - Fix exactly what needs fixing
4. ASK BEFORE BIG MOVES - Schema, folder structure, new dependency -> ask first
5. EVIDENCE BEFORE CLAIMS - Verify before saying "done"
```

## Reference Map

Quick entry point for references: see `references/reference-map.md`.

## Activation Announcement

```
Forge Antigravity: orchestrator | route intent correctly, evidence before claims
```
