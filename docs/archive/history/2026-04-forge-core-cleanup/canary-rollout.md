# Forge Canary Rollout

Archived from `packages/forge-core/references/canary-rollout.md` on 2026-04-22 during forge-core cleanup tranche 2.
This file describes the retired canary rollout guide and remains for historical context only.

## When to read this file

- When auditing older rollout guidance that still referenced the canary profile tooling directly
- When comparing historical release-readiness thresholds against the current target-state docs

> Goal: replace "is it production-ready?" with a canary gate backed by artifacts, explicit thresholds, and a repeatable verdict.

## Rollout Stages

### 1. Controlled Rollout

Target:
- At least 2 real workspaces
- At least 1 day of observation
- No `fail` results
- At most 1 workspace in `warn` state
- No unresolved blocker in the latest run

Evaluation command:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
```

### 2. Broad Readiness

Target:
- At least 3 real workspaces
- At least 6 canary runs in total
- At least 2 distinct observation days
- No `fail` results
- No workspace in `warn` state in the latest run
- No unresolved blocker in the latest run

Evaluation command:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile broad
```

## Workspace Selection

Prioritize three different workspace shapes:
- One workspace with a local router or companion layer
- One workspace that mostly uses Forge core with no local layer
- One workspace with a higher-risk flow where build/debug/deploy/review overlap

Do not choose three workspaces with the same shape. The goal is to catch routing drift and fallback behavior across different surfaces.

## Scenario Pack Suggestions

Each workspace should cover at least:
- natural-language review
- natural-language session or continue flow
- medium or large build flow
- regression-style debug flow
- deploy readiness flow

If the workspace has local companions, also cover:
- runtime-signal-only companion selection
- router checker after changing docs or local skill inventory

## Canonical Workspace Runner

Prefer the automatic runner first. Use `record_canary_result.py` directly only when you need to record a manual result.

```powershell
python scripts/run_workspace_canary.py C:\path\to\workspace --persist
```

The runner persists to:
- `.forge-artifacts/workspace-canaries/`
- `.forge-artifacts/canary-runs/`

## Recording a Canary Result

Successful run:

```powershell
python scripts/record_canary_result.py "Core prompts stable on POS workspace" `
  --workspace lamdi-pos `
  --status pass `
  --scenario "review route" `
  --scenario "build checkout flow" `
  --signal "No misroute seen across 12 prompts" `
  --follow-up "Repeat after next routing change" `
  --persist
```

Warning-level run:

```powershell
python scripts/record_canary_result.py "1 warn on companion fallback wording" `
  --workspace kitchen-display `
  --status warn `
  --scenario "python companion selection" `
  --signal "Route correct but explanation still generic" `
  --follow-up "Tighten activation phrasing" `
  --persist
```

Blocked run:

```powershell
python scripts/record_canary_result.py "Router drift broke local skill selection" `
  --workspace ops-console `
  --status fail `
  --scenario "router check after inventory change" `
  --blocker "Local skill missing from router map" `
  --follow-up "Fix router map and rerun canary" `
  --persist
```

## Canonical Gate

Before calling Forge production-ready:

```powershell
python scripts/verify_bundle.py
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
```

For the broader gate:

```powershell
python scripts/verify_bundle.py --include-canary --canary-profile broad
```

## Verdict Language

Use exactly one of these verdicts:
- `not-ready`: `verify_bundle` failed or the canary profile failed
- `controlled-rollout ready`: `verify_bundle` passed and the controlled-rollout profile passed
- `broad ready`: `verify_bundle` passed and the broad profile passed

Avoid vague verdicts such as:
- "almost production"
- "probably okay"
- "basically usable"

## Failure Handling

If a canary fails:
1. Record the result with `record_canary_result.py`
2. Fix the drift or blocker in the bundle
3. Run `verify_bundle.py` again
4. Rerun the failed workspace canary
5. Raise the verdict only after the latest run is clean
