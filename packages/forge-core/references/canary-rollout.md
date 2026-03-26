# Forge Canary Rollout

> Goal: turn the question "is it production-ready?" into a canary gate with artifact, clear threshold, and repeatable verdict.

## When to read this file

- When Forge core has passed `verify_bundle.py` but you still lack proof of operation on the real host
- When preparing the Forge rollout for the first 2-3 workspaces
- When you need to latch `controlled-rollout ready` or `broad ready`

## Rollout Stages

### 1. Controlled Rollout

Target:
- At least 2 real workspaces
- At least 1 day of observation
- There is no `fail` tremor
- Maximum 1 workspace is in `warn` state
- No more blocker in latest run

Evaluation command:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
```

### 2. Broad Readiness

Target:
- At least 3 real workspaces
- At least 6 canary runs total
- At least 2 different observation days
- There is no `fail` tremor
- There is no latest run workspace in state `warn`
- No more blocker in latest run

Evaluation command:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile broad
```

## Workspace Selection

Prioritize 3 types of workspaces:
- 1 workspace has a local router/companion layer
- 1 workspace mainly uses Forge core, no local layer
- 1 workspace has a more high-risk flow: build/debug/deploy/review interwoven

Do not select all 3 workspaces of the same shape; The goal is to catch misroute and fallback behavior on different surfaces.

## Scenario Pack Suggestions

Each workspace should run at least:
- natural-language review
- session/continue natural-language
- build medium or large
- debug regression-style
- deploy readiness

If the workspace has local companions:
- runtime-signal-only selection
- router checker after changing docs/local skill inventory

## Canonical Workspace Runner

Prioritize using automatic runner first, then add `record_canary_result.py` when needed. Note manual:

```powershell
python scripts/run_workspace_canary.py C:\path\to\workspace --persist
```

Runner self persists:
- `.forge-artifacts/workspace-canaries/`
- `.forge-artifacts/canary-runs/`

## How to score a canary run

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

If there is a warning:

```powershell
python scripts/record_canary_result.py "1 warn on companion fallback wording" `
  --workspace kitchen-display `
  --status warn `
  --scenario "python companion selection" `
  --signal "Route correct but explanation still generic" `
  --follow-up "Tighten activation phrasing" `
  --persist
```

If there is a blocker:

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

Before saying Forge "production-ready":

```powershell
python scripts/verify_bundle.py
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
```

When you want a wider latch:

```powershell
python scripts/verify_bundle.py --include-canary --canary-profile broad
```

## Verdict Language

Use only 1 of 3 verdicts:
- `not-ready`: verify bundle failed or canary profile failed
- `controlled-rollout ready`: verify bundle pass + canary controlled-rollout pass
- `broad ready`: verify bundle pass + canary broad pass

Don't use vague sentences like:
- "almost production"
- "sure it's okay"
- "basically usable"

## Failure Handling

If canary fails:
1. Burn artifact using `record_canary_result.py`
2. Fix drift or blocker in bundle
3. Run `verify_bundle.py` again
4. Rerun workspace canary failed
5. Only raise verdict when the latest run is clean
