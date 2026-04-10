---
name: forge-codex
description: "Forge Codex - Codex-oriented adapter for Forge core. Use when a request needs Forge routing, complexity assessment, skill composition, delivery guardrails, and Codex-friendly workspace integration through AGENTS instructions and local skills."
---

# Forge Codex - Host Adapter

> Forge = delivery discipline + skill composition + evidence before claims.
> Forge must be strong and disciplined enough even if the repo does not have any companion skills or local skills.
> Forge is flexible on small tasks and disciplined on medium and large tasks.
> Forge Codex maps the Forge process-first execution kernel onto Codex through `AGENTS.md`, natural-language-first operator wrappers, and native delegation when the task is safe to split.

---

## Bundle Layout

The tree below reflects the built Codex bundle after overlaying this adapter on top of `forge-core`.
Inherited core files and adapter-added files appear together in one runtime layout.

- `SKILL.md`: entry point for intent routing, skill composition, and delivery guardrails
- `AGENTS.global.md`: canonical global host entry template when Codex should point only to Forge
- `workflows/design/`: planning, architecture, spec-review, visualization
- `workflows/execution/`: build, debug, test, review, refactor, secure, deploy, session, and Codex-native subagent dispatch guidance
- `workflows/operator/`: help, next, run, bump, rollback from core, and thin Codex wrappers for customize/init and natural-language-first guidance
- `domains/`: core domain guidance for frontend and backend
- `data/`: machine-readable registry for intent, matrix, verification profiles, quality profiles, execution pipelines, and lane model policy
- `scripts/`: deterministic tooling for route preview, scoped continuity capture, and optional checks for workspaces with local layers
- `tests/`: regression tests for deterministic scripts and router/tooling contracts
- `references/`: smoke tests, companion contract, read-only reference documents when needed, and Codex operator surface note
- This adapter maps Forge core to Codex surface (`AGENTS.md`, local skills, repo-level instructions)

```text
forge-codex/
├── SKILL.md
├── AGENTS.example.md
├── AGENTS.global.md
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
│ ├── codex-operator-surface.md
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
│ ├── enable_windows_utf8.ps1
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
        ├── dispatch-subagents.md
        ├── quality-gate.md
        ├── refactor.md
        ├── review.md
        ├── secure.md
        ├── session.md
        └── test.md
    └── operator/
        ├── bump.md
        ├── customize.md
        ├── help.md
        ├── init.md
        ├── next.md
        ├── rollback.md
        └── run.md
```

## Host Boundary

- Codex rules live in `AGENTS.md`, system/developer instructions, and the workspace-local skill layout of the Codex host.
- Global Codex host should point to this bundle via `AGENTS.global.md` instead of keeping a parallel legacy router.
- `AGENTS.md` at the workspace root is Codex's primary routing and instruction file. It does not replace `SKILL.md`, but it is an important entry surface for host-loaded context.
- This adapter owns the Codex-facing surface, while routing logic, registry data, verification rules, and canary tooling still come from Forge core.
- If the workspace does not have a local layer, Forge Codex must still run well using the core bundle without waiting for additional repo-specific adapters.

## Independence Rule

- Forge is **global-first orchestrator**.
- New repos, small repos, or repos without local skills still have to use Forge normally using the workflows/domain skills of this bundle.
- Companion skills and workspace routers are **optional augmentation**, not default dependencies.
- If there is no clear companion or local skill, Forge must still proceed with the core bundle instead of waiting for a fuller setup.

---

## Executable Tooling

- Canonical machine-readable source: `data/orchestrator-registry.json`
- Preferences resolver: `scripts/resolve_preferences.py` (adapter-global Forge preferences -> canonical response-style contract, with optional legacy workspace fallback)
- Preferences writer: `scripts/write_preferences.py` (canonical schema persistence for durable customization flows)
- Workspace init skeleton: `scripts/initialize_workspace.py` (repo-neutral bootstrap for reusable init flows)
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
- Default persistent artifacts:
  - `.forge-artifacts/route-previews/`
  - `.forge-artifacts/router-checks/`
- `.forge-artifacts/backend-briefs/`
- `.forge-artifacts/chain-status/`
- `.forge-artifacts/execution-progress/`
- `.forge-artifacts/ui-briefs/`
- `~/.codex/forge-codex/state/preferences.json`
- `~/.codex/forge-codex/state/extra_preferences.json`
- `.brain/decisions.json`
- `.brain/learnings.json`

When you need detailed command examples or artifact behavior, read `references/tooling.md`.

---

## Response Personalization

- At the start of each new thread, resolve preferences before the first substantive user-facing reply so adapter-global state is restored automatically.
- Forge resolves preferences via core engine `scripts/resolve_preferences.py` from Codex-global split state: canonical fields in `state/preferences.json`, adapter extras in `state/extra_preferences.json`, and only falls back to `.brain/preferences.json` for legacy workspaces.
- The canonical schema includes `technical_level`, `detail_level`, `autonomy_level`, `pace`, `feedback_style`, and `personality`.
- Adapter-global extra preferences may carry host-native response constraints such as `language`, `orthography`, honorific rules, or custom writing rules. Workspace `.brain/preferences.json` remains a workspace-local override or legacy fallback.
- When `language` resolves to `vi`, `forge-codex` should respond in Vietnamese with full diacritics. Accent-stripped or mojibake Vietnamese is an encoding defect, not an allowed style variant.
- `forge-codex` should keep customization natural-language first on top of this schema. By default, it should not rely on slash-command-heavy wrappers.
- This adapter must not fork key names or response-style semantics of the core.

---

## Operator Guidance

- `forge-codex` should expose `help/next` as natural-language first, with slash commands as optional aliases.
- Guidance still resolves from core navigator `scripts/resolve_help_next.py`.
- The adapter must not fork core's repo-first contract or its "one clear next step" rule.
- `forge-codex` should expose `run` as natural-language first, with slash commands as optional aliases.
- Command execution guidance still resolves from core `scripts/run_with_guidance.py`. The adapter must not fork the semantics of `state`, `command_kind`, or `suggested_workflow`.
- Error translation still resolves from core `scripts/translate_error.py`. This adapter must not fork the category or pattern database.
- `bump` and `rollback` should stay natural-language first, with aliases remaining optional, while preserving the core's user-requested/inference-justified and risk-first contract.
- If you need to customize/init in Codex, you still have to use `scripts/write_preferences.py` and `scripts/initialize_workspace.py` instead of creating host-local schema.

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

## Codex Operator Surface

Primary entry points:

|Surface | Codex styles | Core contract|
|---------|-------------|---------------|
|`help` | natural-language first, `/help` is only an optional alias | `scripts/resolve_help_next.py --mode help`|
|`next` | natural-language first, `/next` is only an optional alias | `scripts/resolve_help_next.py --mode next`|
|`run` | natural-language first, `/run` is only an optional alias | `scripts/run_with_guidance.py`|
|`delegate` | natural-language first, `/delegate` is only an optional alias | `workflows/execution/dispatch-subagents.md`|
|`bump` | natural-language first, explicit-or-inferred | `scripts/prepare_bump.py`|
|`rollback` | natural-language first, risk-first | `scripts/resolve_rollback.py`|
|`customize` | thin preference update flow | `scripts/resolve_preferences.py` + `scripts/write_preferences.py`|
|`init` | thin workspace bootstrap flow | `scripts/initialize_workspace.py`|

Compatibility rules:

- Alias ​​only exists if it reduces friction clearly.
- Do not add legacy session wrappers for Codex adapters.
- Mapping details: `references/codex-operator-surface.md`.

## Codex Multi-Agent Delegation

- When route/build select `parallel-safe` or independent reviewer lane and bundle registry tells host to have native subagents, load `workflows/execution/dispatch-subagents.md`.
- This workflow maps Forge's lane policy onto Codex runtime primitives (`spawn_agent`, independent reviewer lanes, fresh packets). It does not replace `build`, `debug`, `review`, or `spec-review`.
- By default, keep new packets and clear ownership instead of forking the entire thread context for the subagent.

---

## Intent Detection

When receiving a prompt from the user, classify the intent:

|Intent | Trigger keywords | Example|
|--------|------------------|-------|
|**BUILD** | add, create, implement, feature, code | "Add payment feature"|
|**DEBUG** | error, bug, fix, fix, error, crash | "Fix the login failure"|
|**OPTIMIZE** | refactor, optimize, clean, tidy up | "Refactor file is too long"|
|**DEPLOY** | deploy, release, production, rollout | "Deploy to Vercel"|
|**REVIEW** | review, evaluate, check, audit | "Review code before merging"|
|**VISUALIZE** | ui, ux, mockup, wireframe, screen, layout | "Checkout screen sketch"|
|**SESSION** | continue, resume, context, handover | "Continue unfinished business"|

**When the user uses `/shortcut`:** Map according to the action surface and workflow aliases that the Codex workspace is declared in `AGENTS.md`.
Canonical source for intent keywords and chains: `data/orchestrator-registry.json`.

Signals like `brainstorm`, locale-specific brainstorming phrases in active routing locales, `options`, `approach`, and `tradeoff` do not create new intents. They activate the **brainstorm gate** before `plan` when the task is vague or complex enough.

---

## Complexity Assessment

|Level | Criteria | Example|
|-------|----------|-------|
|**small** | <=2 files, small blast radius, clear requirements | Fix typo, edit CSS, change 1 field|
|**medium** | 3-10 files, with behavior changes or need for assumption | Add filter, CRUD endpoint|
|**large** | >10 new files or features/modules, extensive data flow | Payment, auth flow, new modules|

Doubt small or medium -> default **medium**.
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
**Lane model policy:** use abstract tiers `cheap / standard / capable` by lane instead of pushing every step to the same capability level.

**Domain skills** (`frontend`, `backend`) added when the task involves UI or API/database/service layer.
**Companion runtime/language skills** (Python, Java, Go, .NET, framework-specific) are optional augmentations when the repo/framework is already known. Forge should still run well without them.
Companion skill contract: see `references/companion-skill-contract.md` when you are actually adding a runtime/framework layer.
If the workspace has `AGENTS.md` or a router doc that points to local skills, use that router as the source of truth for this extension layer. If not, Forge should continue with its own bundle.
To preview routing deterministically for a specific prompt, run `scripts/route_preview.py`.

### How to load skills

```
1. Detect intent + complexity
2. Look up the matrix -> the list of Forge skills required
3. Select the execution pipeline and lane model tiers if the task is large or risky enough
4. Choose the Forge chain that is sufficient to solve the task with this bundle itself
5. Check repo signals (`package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`,...)
6. If a suitable companion skill exists and truly improves accuracy -> add it to the chain
7. If the workspace has a router doc for local skills -> use it as an extension layer, not a Forge replacement
8. Announce to the user: "Forge: [intent] | [complexity] | Skills: [list]"
9. Load the first skill
10. Complete the important quality gate
11. Only move to the next skill if needed
```

You do not need to load the full chain if the task is already resolved safely.
Companion/local skills cannot override Forge's verification/evidence gate.

**Minimal routing policy:** with `REVIEW`, `SESSION`, and task `small`, Forge prioritizes prompt-led routing. Repo signals at this time will not automatically pull additional domain skills, local companions, or escalate profiles if the prompt does not clearly state the need.

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
- Forge uses `lane model tiers` to optimize costs: navigation/triage can be cheaper than spec-review or release gates.
- Forge uses `quality-gate` as canonical source for the evidence response contract, the global `Skill selection:` explanation, the global `Skills used:` footer, and anti-rationalization.
- The `spec-review` loop allows at most `3` revision rounds for the same packet. Beyond that threshold, the status must become `blocked`.

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
|customize | `workflows/operator/customize.md` | flexible | DO NOT FORK THE CORE PREFERENCES SCHEMA OR WRITE HOST-LOCAL KEYS|
|init | `workflows/operator/init.md` | flexible | DO NOT OVERWRITE EXISTING REPO FILES DURING BOOTSTRAP|

**Rigid skills:** do not ignore evidence and quality gate.
**Flexible skills:** adapt according to context, but still have to be clear about output and next steps.

---

## Global Resilience

### Auto-Retry
```
Network error, timeout, file write:
1. Retry once
2. Retry a second time if the error looks transient
3. If it still fails -> notify the user + propose a fallback
```

### Long-Running Work
```
If the task drags on or a command keeps failing:
1. Tell the user where the work is stuck
2. Summarize what has been tried
3. Propose the safest next step
```

### Error Translation (when needed)

|Original error | Translate|
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
1. DO ONLY WHAT WAS REQUSTED - Do not expand scope on your own
2. ONE THING AT A TIME - Finish A before jumping to B
3. MINIMAL CHANGE - Edit exactly the part that needs to change
4. ASK BEFORE BIG CHANGES - New schema, folder structure, or dependency -> ask first
5. EVIDENCE BEFORE CLAIMS - Verify before saying "done"
```

## Reference Map

Quick entry point for references: see `references/reference-map.md`.

## Activation Announcement

```
Forge Codex: orchestrator | route the right intent, keep evidence before claims
```
