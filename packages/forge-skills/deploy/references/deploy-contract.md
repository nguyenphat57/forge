# Deploy Contract

Use this reference when `forge-deploy` is active and the deploy boundary needs a concrete checklist.

## Required Fields

- **Target:** staging, production, preview, or another named environment
- **Command source:** repo script, platform runbook, CI workflow, or explicit operator command
- **Preflight evidence:** latest build/test/smoke proof that supports a deploy-facing decision
- **Post-deploy proof:** the exact smoke check, URL, health probe, or artifact check that confirms the rollout
- **Rollback path:** command, owner, or runbook path for immediate recovery

## Blocking Rules

Stop and report blocked state when:

- the target is unclear
- the repo does not name a deploy command or source of truth
- pre-deploy verification is stale or missing
- the rollout changes external state and no explicit confirmation was given
- rollback path is missing for a risky or public deploy

## Confirmation Rule

Readiness analysis does not need explicit confirmation.

Any command that changes a live environment does. The confirmation must happen before the deploy action, not after the command is already staged.

## Boundary Rule

`forge-deploy` does not own:

- semver inference
- `VERSION` edits
- `CHANGELOG.md` authoring
- PR creation or merge strategy

Route those concerns to the owning sibling skill instead of blending them into deploy.

