# Deploy Checks

Use this reference when `forge-deploy` needs concrete preflight or post-deploy evidence.

## Pre-Deploy Checks

- latest targeted verification still reflects the deploy candidate
- working tree and artifact state are understood
- target environment is explicit
- deploy command source is documented
- config, secrets, migrations, and feature-flag assumptions are named
- rollback path exists or missing rollback is reported as a blocker

## Post-Deploy Checks

- smoke test or health probe passes
- deployed version, image tag, or commit is visible where expected
- critical user path works
- logs, service status, or telemetry do not show immediate deploy failure

## Failure Handling

If a pre-deploy check fails:

- do not run the deploy command
- report blocked status
- name the failing proof and next action

If a post-deploy check fails:

- do not claim shipped or deployed
- report the exact failing proof
- activate rollback guidance or `forge-systematic-debugging`

## Evidence Standard

Verbal reassurance is not evidence.

Use commands, URLs, artifacts, health checks, or explicit runbook output that can be inspected again.

