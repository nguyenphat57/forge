# Forge Tooling

> Use this when you want to turn Forge routing and verification from prose into runnable checks.

## Registry Canonical Source

- The orchestrator's machine-readable file is located at `data/orchestrator-registry.json`
- This is the canonical source for:
- intent keywords. intent keywords
- skill composition matrix
- complexity hints
- verification profiles
- runtime hints
- execution modes
- execution pipelines
- lane model policy
- evidence response contract
- completion states

## Preferences Resolver

When you need to inspect or validate response-style preferences according to Forge's general schema:

```powershell
python scripts/resolve_preferences.py
```

Explicit files:

```powershell
python scripts/resolve_preferences.py --preferences-file C:\path\to\adapter-state\state\preferences.json --format json
```

Strict validation:

```powershell
python scripts/resolve_preferences.py --workspace C:\path\to\workspace --strict
```

The script returns:
- source of preferences (explicit, global, workspace-legacy, or defaults)
- canonical preferences after normalization
- response-style contract resolved
- warnings if the payload has strange fields or invalid values

Schema and boundary doc: see `personalization.md`.

## Preferences Persistence

When you need to update adapter-global Forge preferences while still keeping Forge's canonical schema:

```powershell
python scripts/write_preferences.py --technical-level newbie --pace fast
python scripts/write_preferences.py --feedback-style direct --apply
```

The script:
- merge update into existing preferences by default
- reuse legacy `.brain/preferences.json` as migration base if adapter-global file does not exist and passes `--workspace`
- support `--replace` to reset fields without returning to defaults
- return `changed_fields`, target preferences, and the response-style contract after normalization

Detailed semantics: see `personalization.md`.

## Workspace Init

When you need to preview or create a minimal Forge skeleton for a new workspace:

```powershell
python scripts/initialize_workspace.py --workspace C:\path\to\workspace
python scripts/initialize_workspace.py --workspace C:\path\to\workspace --seed-preferences --apply
```

The script:
- classify workspace to `greenfield` or `existing`
- create `.brain/`, `docs/plans/`, `docs/specs/`, and `.brain/session.json`
- optionally seed adapter-global split preferences state (`state/preferences.json` + `state/extra_preferences.json`)
- returns recommended next workflow (`brainstorm` or `plan`)

Detailed semantics: see `workspace-init.md`.

## Change Artifacts And Packet Checks

When medium or risky work needs durable change artifacts instead of chat-only context:

```powershell
python scripts/change_artifacts.py start "Add checkout retry" --workspace C:\path\to\workspace --task "Implement retry guard in checkout flow" --verification "pytest tests/test_checkout.py -k retry"
python scripts/change_artifacts.py status --workspace C:\path\to\workspace --slug add-checkout-retry --state ready-for-review --verified "pytest tests/test_checkout.py -k retry"
python scripts/change_artifacts.py archive --workspace C:\path\to\workspace --slug add-checkout-retry --decision "Merged after review"
```

The script:
- create active change artifacts including `specs/<slug>/spec.md`
- persist `status.json` with verification state
- merge archive knowledge back into the durable spec index

Use `generate_requirements_checklist.py` when requirements need a quick ambiguity/measurability/testability pass:

```powershell
python scripts/generate_requirements_checklist.py --requirement "Checkout retry must recover failed payments within 3 attempts and verify with a repeatable scenario." --format json
```

Use `check_spec_packet.py` before build when the packet may still be missing a source of truth, first slice, baseline proof, proof-before-progress, or reopen condition:

```powershell
python scripts/check_spec_packet.py --source docs\plans\checkout-plan.md --source .forge-artifacts\changes\active\checkout-retry\implementation-packet.md --format json
```

For an end-to-end example, read `artifact-driven-change-flow.md`.

## Host Artifact Generator

When host-global templates need to stay generated from a canonical source instead of hand-maintained overlays:

```powershell
python scripts/generate_host_artifacts.py --check --format json
python scripts/generate_host_artifacts.py --apply
```

Canonical inventory lives in:

```text
docs/architecture/host-artifacts-manifest.json
```

The loader entry point used by the generator lives in:

```text
scripts/host_artifact_specs.py
```

Current generated outputs:

```text
packages/forge-codex/overlay/AGENTS.global.md
packages/forge-codex/overlay/workflows/execution/session.md
packages/forge-codex/overlay/workflows/operator/help.md
packages/forge-codex/overlay/workflows/operator/next.md
packages/forge-codex/overlay/workflows/operator/run.md
packages/forge-codex/overlay/workflows/operator/bump.md
packages/forge-codex/overlay/workflows/operator/rollback.md
packages/forge-codex/overlay/workflows/operator/customize.md
packages/forge-codex/overlay/workflows/operator/init.md
packages/forge-antigravity/overlay/GEMINI.global.md
```

If `--check` fails, refresh the generated files before running `build_release.py` or `verify_repo.py`.

## Runtime Tool Resolver

When a host bundle needs to call `forge-browse` or `forge-design` without hardcoding the install path:

```powershell
python scripts/resolve_runtime_tool.py forge-browse --format json
python scripts/invoke_runtime_tool.py forge-design render-brief .forge-artifacts/ui-briefs/<project-slug>/visualize --screen dashboard
python scripts/invoke_runtime_tool.py --doctor forge-design
```

The resolver checks:
- explicit `--tool-target` override
- tool-specific env override such as `FORGE_BROWSE_ROOT`
- adapter-global runtime tool registry in `state/runtime-tools.json`
- `runtime_tools_relative_path` from bundle build/install manifest when present
- local sibling bundle path in `packages/` or `dist/` when running from source

Register runtime tool targets during install with:

```powershell
python scripts/install_bundle.py forge-browse --target C:\tools\forge-browse --register-codex-runtime --register-gemini-runtime
python scripts/install_bundle.py forge-design --target C:\tools\forge-design --register-codex-runtime --register-gemini-runtime
```

## Help/Next Navigator

When you need to resolve operator based on repo state instead of guidance recap ritual:

```powershell
python scripts/resolve_help_next.py --workspace C:\path\to\workspace --mode help
python scripts/resolve_help_next.py --workspace C:\path\to\workspace --mode next --format json
```

Script to read:
- `git status` if that workspace is a private git root
- `docs/plans/` and `docs/specs/`
- `.forge-artifacts/workflow-state/<project>/latest.json` when execution, chain, UI, run, or quality-gate tools have already persisted state
- `.forge-artifacts/workflow-state/<project>/packet-index.json` for low-cost continuity resume when full state is not required yet
- `.brain/session.json` and `.brain/handover.md` if available
- `README`
- adapter-global split preferences state via `resolve_preferences.py` to adapt response style

The script checks:
- `current_stage`
- `current_focus`
- `suggested_workflow`
- `recommended_action`
- Maximum 2 alternatives
- evidence and warnings

Detailed semantics: see `help-next.md`.

## Operator Entry Points

When you need a durable repo snapshot, health diagnosis, or brownfield map before choosing the next workflow:

```powershell
python scripts/dashboard.py --workspace C:\path\to\workspace --persist --format json
python scripts/doctor.py --workspace C:\path\to\workspace --format json
python scripts/map_codebase.py --workspace C:\path\to\workspace --format json
```

Default persisted artifacts:

```text
.forge-artifacts/dashboard/latest.json
.forge-artifacts/dashboard/history/
.forge-artifacts/doctor/latest.json
.forge-artifacts/doctor/history/
.forge-artifacts/codebase/summary.json
.forge-artifacts/codebase/summary.md
.forge-artifacts/codebase/focus/<area>.md
```

Typical follow-up:
- run `dashboard.py` when resuming work and then use `help` or `next`
- run `doctor.py` when Forge/runtime wiring looks suspicious, then rerun `map_codebase.py` if health is usable
- run `map_codebase.py` before the first brownfield edit, then feed that output into `plan`, `spec-review`, or `build`

## Run Guidance

When you need to run the actual command and route the next step from the output:

```powershell
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --project-name "Example Project" --persist --output-dir C:\path\to\workspace -- npm run build
```

The script returns:
- `state`
- `command_kind`
- `suggested_workflow`
- `recommended_action`
- `stdout_excerpt` / `stderr_excerpt`
- `readiness_detected`
- evidence and warnings

If using `--persist`, the default artifact is located at:

```text
.forge-artifacts/run-reports/
.forge-artifacts/workflow-state/<project-slug>/latest.json
.forge-artifacts/workflow-state/<project-slug>/events.jsonl
.forge-artifacts/workflow-state/<project-slug>/packet-index.json
```

Detailed semantics: see `run-guidance.md`.

## Quality Gate Recorder

When you need to close a go / no-go decision from fresh evidence and carry that decision into `help/next`:

```powershell
python scripts/record_quality_gate.py --workspace C:\path\to\workspace --profile standard --target-claim ready-for-merge --decision conditional --evidence "pytest tests/test_checkout.py" --response "I verified: ..." --why "..." --next-evidence "Run merge-readiness smoke" --persist --output-dir C:\path\to\workspace
python scripts/record_quality_gate.py --workspace C:\path\to\workspace --profile release-critical --target-claim deploy --decision go --evidence "python scripts/build_release.py --format json" --response "I verified: ..." --why "..." --persist
```

The script returns:
- `status`
- `profile`
- `target_claim`
- `decision`
- `evidence_read`
- `response`
- `why`
- `next_evidence`
- `risks`

If using `--persist`, the default artifacts are:

```text
.forge-artifacts/quality-gates/<project-slug>/
.forge-artifacts/workflow-state/<project-slug>/latest.json
.forge-artifacts/workflow-state/<project-slug>/events.jsonl
```

`record_quality_gate.py` now also consumes the latest active change, review, and `verify-change` artifacts when the target claim requires them.

## Worktree Prep And Verify Change

When risky build work should start from an isolated baseline instead of the current dirty tree:

```powershell
python scripts/prepare_worktree.py --workspace C:\path\to\workspace --name checkout-retry --baseline-command "python -m pytest tests/test_checkout.py -k retry" --persist --format json
```

The script:
- create or reuse an isolated git worktree
- make project-local worktree roots ignore-safe
- run optional setup commands
- run baseline commands and report `ready` or `blocked`

When the slice is implemented and the artifacts are updated, verify the change packet itself:

```powershell
python scripts/verify_change.py --workspace C:\path\to\workspace --slug checkout-retry --persist --format json
```

`verify_change.py` scores:
- completeness
- correctness
- coherence
- evidence strength
- residual risk

Use it before `ready-for-merge`, `done`, or `deploy` claims so `quality-gate` can consume a persisted `PASS`.

## Error Translation

When you need to translate stderr/raw error into a more readable summary while still preserving enough context for debugging:

```powershell
python scripts/translate_error.py --error-text "Module not found: payments.service"
python scripts/translate_error.py --input-file C:\path\to\stderr.txt --format json
```

The script:
- Sanitize tokens, secrets, and basic sensitive paths
- match the input against the deterministic pattern database
- return `human_message`, `suggested_action`, and `category`
- generic fallback if there is no suitable pattern

Detailed semantics: see `error-translation.md`.

## Bump Preparation

When you need to finalize a new version in the user-requested release flow:

```powershell
python scripts/prepare_bump.py --workspace C:\path\to\workspace
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump minor
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump 2.0.0 --apply --release-ready
```

The script:
- read `VERSION`
- infer or get explicit semver bump
- calculate `target_version`
- preview or update `VERSION` + `CHANGELOG.md`
- returns the next verification command

Detailed semantics: see `bump-release.md`.

## Rollback Guidance

When you need a safe rollback plan instead of blind-revert:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high
```

The script:
- select recovery strategy according to scope/risk
- warn of data-loss risk when needed
- return the suggested workflow and verification checklist

Detailed semantics: see `rollback-guidance.md`.

## UI Brief Generator

When the task is `frontend` or `visualize` and needs an explicit first artifact before coding/mockup:

```powershell
python scripts/generate_ui_brief.py "Refresh checkout for tablet POS" `
  --mode frontend `
  --stack react-vite `
  --platform tablet `
  --screen checkout
```

Or:

```powershell
python scripts/generate_ui_brief.py "Explore calmer kitchen dashboard direction" `
  --mode visualize `
  --stack mobile-webview `
  --platform tablet `
  --screen kitchen-dashboard
```

### Persist UI brief

```powershell
python scripts/generate_ui_brief.py "..." --mode frontend --persist --project-name "LamDiFood POS" --screen checkout
```

Default Artifact:

```text
.forge-artifacts/ui-briefs/<project-slug>/<mode>/
```

Brief pattern details: see `ui-briefs.md`.

## Backend Brief Generator

When the backend task is medium/large or touches contract/schema/job/event:

```powershell
python scripts/generate_backend_brief.py "Add bulk order cancellation endpoint" `
  --pattern sync-api `
  --runtime node-service `
  --surface cancel-orders
```

Or:

```powershell
python scripts/generate_backend_brief.py "Reconcile failed payouts in worker" `
  --pattern async-job `
  --runtime python-service `
  --surface payout-reconcile
```

### Persist backend brief

```powershell
python scripts/generate_backend_brief.py "..." --pattern sync-api --persist --project-name "Example Project" --surface cancel-orders
```

Default Artifact:

```text
.forge-artifacts/backend-briefs/<project-slug>/
```

Brief pattern details: see `backend-briefs.md`.

## Backend Brief Checker

When the brief backend has been persisted and needs quick verification:

```powershell
python scripts/check_backend_brief.py .forge-artifacts/backend-briefs/<project-slug> --surface cancel-orders
```

Default Artifact report:

```text
.forge-artifacts/backend-brief-checks/
```

## UI Brief Checker

Once the brief has been persisted and need to quickly verify that the artifact has all required sections:

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
```

Default Artifact report:

```text
.forge-artifacts/ui-brief-checks/
```

## UI Progress Tracker

When the frontend/visualize task spans multiple stages:

```powershell
python scripts/track_ui_progress.py "Checkout tablet refresh" --mode frontend --stage implementation --status active
```

Default Artifact:

```text
.forge-artifacts/ui-progress/<mode>/
```

The tracker also refreshes:

```text
.forge-artifacts/workflow-state/<project-slug>/latest.json
.forge-artifacts/workflow-state/<project-slug>/events.jsonl
```

## Route Preview

When you want to preview the route for a prompt before loading the skill chain:

```powershell
python scripts/route_preview.py "Fix outbox bi ket sau khi app online lai" `
  --repo-signal package.json `
  --repo-signal src/services/syncManager.ts
```

If the workspace has local layers, add `--workspace-router` as an optional input:

```powershell
python scripts/route_preview.py "..." `
  --workspace-router C:\path\to\workspace\.agent\workspace-skill-map.md
```

`--workspace-router` accepts both `AGENTS.md` and the resolved router map.

The script returns:
- intent
- complexity
- Forge skills
- host skills exposed by the current bundle (if any)
- execution mode recommendation
- execution pipeline recommendation
- delegation strategy recommendation
- lane model tier recommendations
- quality profile recommendation
- domain skills
- local companion candidates (if the workspace has a local layer)
- verification-first plan

For `REVIEW`, `SESSION`, and task `small`, preview prioritizes minimal path: repo signals do not automatically pull additional domain/local companions if the prompt does not explicitly say so.

### Persist route preview

```powershell
python scripts/route_preview.py "..." --persist
```

Default Artifact:

```text
.forge-artifacts/route-previews/
```

Example high-risk build:

```powershell
python scripts/route_preview.py "Implement auth migration with public API contract change" `
  --repo-signal package.json `
  --repo-signal migrations `
  --repo-signal api/
```

Expected output:
- `Execution pipeline: Implementer -> spec reviewer -> quality reviewer`
- `Lane model tiers`
- `Spec-review loop cap: 3` when applicable

## Scoped Continuity Capture

When there is a decision or learning that is stable enough to be saved according to scope:

```powershell
python scripts/capture_continuity.py "Compatibility window must stay at 1 release" `
  --kind decision `
  --scope orders-api `
  --evidence "docs/DESIGN.md"
```

Default Artifact:

```text
.brain/decisions.json
.brain/learnings.json
```

## Execution Progress Tracker

When a medium/large build task spans multiple checkpoints:

```powershell
python scripts/track_execution_progress.py "Implement offline order reconciliation" `
  --mode checkpoint-batch `
  --stage integration `
  --lane implementer `
  --model-tier capable `
  --proof "failing reconciliation reproduction" `
  --status active `
  --done "Added reconciliation service skeleton" `
  --next "Wire retry policy into sync manager" `
  --risk "End-to-end verification still pending"
```

Persist artifacts:

```powershell
python scripts/track_execution_progress.py "..." --mode checkpoint-batch --stage integration --persist --project-name "Example Project"
```

Default Artifact:

```text
.forge-artifacts/execution-progress/<project-slug>/
```

The tracker also refreshes:

```text
.forge-artifacts/workflow-state/<project-slug>/latest.json
.forge-artifacts/workflow-state/<project-slug>/events.jsonl
```

Important new fields:
- `lane`
- `model-tier`
- `proof-before-progress`

## Chain Status Tracker

When a long chain goes through many skills/stages and needs to see the total status:

```powershell
python scripts/track_chain_status.py "Checkout rewrite flow" `
  --project-name "Example Project" `
  --current-stage spec-review `
  --completed-stage brainstorm `
  --completed-stage plan `
  --next-stage build `
  --active-skill build `
  --active-skill spec-review `
  --active-lane implementer `
  --active-lane spec-reviewer `
  --lane-model implementer=capable `
  --lane-model spec-reviewer=capable `
  --review-iteration 2 `
  --max-review-iterations 3 `
  --gate-decision conditional `
  --risk "Large migration verification still pending"
```

Persist artifacts:

```powershell
python scripts/track_chain_status.py "..." --current-stage build --persist --project-name "Example Project"
```

Default Artifact:

```text
.forge-artifacts/chain-status/<project-slug>/
```

The tracker also refreshes:

```text
.forge-artifacts/workflow-state/<project-slug>/latest.json
.forge-artifacts/workflow-state/<project-slug>/events.jsonl
```

Important new fields:
- `active-lanes`
- `lane-model`
- `review-iteration`
- `max-review-iterations`

## Workspace Router Check

Only used when the workspace actually has a local skill layer or router docs.

When editing `AGENTS.md`, workspace map, or local skills:

```powershell
python scripts/check_workspace_router.py C:\path\to\workspace
```

Checker will compare:
- `AGENTS.md`
- workspace skill map
- local skills under `.agent/skills/`
- routing smoke tests
- local-skill maintenance doc

### Persist router check

```powershell
python scripts/check_workspace_router.py C:\path\to\workspace --persist
```

Default Artifact:

```text
.forge-artifacts/router-checks/
```

## Regression Tests

When changing routing logic, companion detection, or router checker:

```powershell
python -m unittest discover -s tests -v
```

Currently the regression suite focuses on:
- route preview for review/session/local-companion cases
- workspace router checker for explicit router doc names

## Smoke Matrix Runner

When you need to run executable smoke cases instead of just reading the checklist:

```powershell
python scripts/run_smoke_matrix.py
```

Options:

```powershell
python scripts/run_smoke_matrix.py --suite route-preview
python scripts/run_smoke_matrix.py --suite router-check --format json
```

This runner reads the fixture from `tests/fixtures/` and calls CLI scripts to catch drift at the entry point level.
Smoke suite currently covers:
- route preview
- workspace router check
- preferences resolution
- help/next navigator
- run guidance
- error translation
- bump preparation
- rollback guidance

## Verify Bundle

Standard release/CI command for Forge bundle:

```powershell
python scripts/verify_bundle.py
```

Current pipeline:
- `py_compile` for scripts + tests
- `unittest discover -s tests -v`
- `run_smoke_matrix.py`

If there are real soak/canary artifacts:

```powershell
python scripts/verify_bundle.py --include-canary --canary-profile controlled-rollout
python scripts/verify_bundle.py --include-canary --canary-profile broad
```

## Canary Rollout Tooling

Run canary pack automatically on real workspace:

```powershell
python scripts/run_workspace_canary.py C:\path\to\workspace --persist
```

This Runner will:
- detect common repo signals
- run core route pack (`review`, `session`, `build`, `debug`, `deploy`)
- run router check if workspace has `AGENTS.md`
- run runtime-signal local companion check if workspace has local skills
- persist both detail artifact and canary-run summary

Record a canary run:

```powershell
python scripts/record_canary_result.py "Core prompts stable on POS workspace" `
  --workspace lamdi-pos `
  --status pass `
  --scenario "review route" `
  --persist
```

Readiness rating:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile broad
```

Broad readiness now also requires at least two different days of observation, not just enough runs.

Detailed runbook: see `canary-rollout.md`.

## When to use which tool?

- Preview a single task: `route_preview.py`
- Audit drift of workspace router: `check_workspace_router.py` when workspace has local layer
- Capture decision/learning scoped, evidence-backed: `capture_continuity.py`
- Create or check first artifact for backend: `generate_backend_brief.py` / `check_backend_brief.py`
- Check overall chain/go-no-go: `track_chain_status.py` + `record_quality_gate.py` + `quality-gate.md`
- Track checkpoint for long builds: `track_execution_progress.py`
- Full chain track length: `track_chain_status.py`
- Run smoke suite entry-point: `run_smoke_matrix.py`
- Run full release gate locally/CI: `verify_bundle.py`
- Run canary pack automatically on real workspace: `run_workspace_canary.py`
- Record soak/canary artifact from real workspace: `record_canary_result.py`
- Final verdict rollout from real artifact: `evaluate_canary_readiness.py`
- Resolve, invoke, or run doctor on registered runtime tools: `resolve_runtime_tool.py` / `invoke_runtime_tool.py --doctor`
- Only read policy and examples: return to `SKILL.md` or `references/companion-skill-contract.md`
