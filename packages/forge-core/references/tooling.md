# Forge Tooling

> Deep reference for the current kernel-only tooling surface. Historical runtime-tool and canary-era commands are archived and are not part of the active contract.

## Canonical Source

- Machine-readable routing and workflow policy: `data/orchestrator-registry.json`
- Current maintainer entrypoints: `reference-map.md` and `kernel-tooling.md`
- Canonical host artifact inventory: `docs/architecture/host-artifacts-manifest.json`

## Preferences And Personalization

Inspect or validate response-style preferences:

```powershell
python scripts/resolve_preferences.py
python scripts/resolve_preferences.py --preferences-file C:\path\to\adapter-state\state\preferences.json --format json
python scripts/resolve_preferences.py --workspace C:\path\to\workspace --strict
```

Update adapter-global preferences:

```powershell
python scripts/write_preferences.py --technical-level newbie --pace fast
python scripts/write_preferences.py --feedback-style direct --apply
```

Detailed semantics: see `personalization.md`.

## Workspace Bootstrap

Preview or create a minimal Forge skeleton:

```powershell
python scripts/initialize_workspace.py --workspace C:\path\to\workspace
python scripts/initialize_workspace.py --workspace C:\path\to\workspace --seed-preferences --apply
```

Detailed semantics: see `workspace-init.md`.

## Packet Checks And Planning Validation

Generate a quick ambiguity or measurability pass:

```powershell
python scripts/generate_requirements_checklist.py --requirement "Checkout retry must recover failed payments within 3 attempts and verify with a repeatable scenario." --format json
```

Check whether a plan or spec packet is build-ready:

```powershell
python scripts/check_spec_packet.py --source docs\plans\checkout-plan.md --source .forge-artifacts\execution-progress\checkout\latest.json --format json
```

## Host Artifact And Overlay Generation

Refresh generated host artifacts from canonical sources:

```powershell
python scripts/generate_host_artifacts.py --check --format json
python scripts/generate_host_artifacts.py --apply
```

Refresh generated adapter `SKILL.md` artifacts:

```powershell
python scripts/generate_overlay_skills.py --check
python scripts/generate_overlay_skills.py --apply
```

## Operator State And Session Tools

Resolve operator guidance from repo state:

```powershell
python scripts/resolve_help_next.py --workspace C:\path\to\workspace --mode help --format json
python scripts/resolve_help_next.py --workspace C:\path\to\workspace --mode next --format json
```

Persist or restore session context:

```powershell
python scripts/session_context.py save --workspace C:\path\to\workspace --task "Finish checkout retry slice"
python scripts/session_context.py resume --workspace C:\path\to\workspace --format json
```

Run a command and route the next step from real output:

```powershell
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
```

Close a quality gate from fresh evidence:

```powershell
python scripts/record_quality_gate.py --workspace C:\path\to\workspace --profile standard --target-claim ready-for-merge --decision conditional --evidence "pytest tests/test_checkout.py" --response "I verified: ..." --why "..." --persist
```

Detailed semantics: see `help-next.md` and `run-guidance.md`.

## Release And Recovery Helpers

Prepare a version bump:

```powershell
python scripts/prepare_bump.py --workspace C:\path\to\workspace
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump minor
```

Resolve rollback guidance:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
```

Prepare an isolated worktree:

```powershell
python scripts/prepare_worktree.py --workspace C:\path\to\workspace --name checkout-retry --baseline-command "python -m pytest tests/test_checkout.py -k retry" --format json
```

Translate raw error output:

```powershell
python scripts/translate_error.py --error-text "Module not found: payments.service"
```

## Brief Checkers

Forge still ships checkers for persisted brief artifacts:

```powershell
python scripts/check_backend_brief.py .forge-artifacts/backend-briefs/<project-slug> --surface cancel-orders
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
```

Use `backend-briefs.md` and `ui-briefs.md` when a repo already carries those artifacts. Forge no longer ships the older brief generators as part of the current kernel-only surface.

## Routing And Continuity

Preview route decisions:

```powershell
python scripts/route_preview.py "Fix outbox bi ket sau khi app online lai" --repo-signal package.json
```

Capture durable decisions or learnings:

```powershell
python scripts/capture_continuity.py "Compatibility window must stay at 1 release" --kind decision --scope orders-api --evidence "docs/DESIGN.md"
```

Track execution checkpoints:

```powershell
python scripts/track_execution_progress.py "Implement offline order reconciliation" --mode checkpoint-batch --stage integration --status active
python scripts/track_chain_status.py "Checkout rewrite flow" --current-stage build --active-skill build --persist --project-name "Example Project"
python scripts/track_ui_progress.py "Checkout tablet refresh" --mode frontend --stage implementation --status active
```

## Router And Smoke Checks

Check a workspace router when the repo has local layers:

```powershell
python scripts/check_workspace_router.py C:\path\to\workspace
python scripts/check_workspace_router.py C:\path\to\workspace --persist
```

Run smoke cases:

```powershell
python scripts/run_smoke_matrix.py
python scripts/run_smoke_matrix.py --suite route-preview
```

Verify a built bundle:

```powershell
python scripts/verify_bundle.py
python scripts/verify_bundle.py --format json
```

## Historical Notes

- Historical runtime-tool resolver/invoker commands and canary-era commands are not part of the current kernel-only surface.
- If a historical doc references those commands, treat it as archive context unless `docs/current/` explicitly points to it.
