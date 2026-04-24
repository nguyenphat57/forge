# Rollback Guidance

Use this reference when a deploy fails, post-deploy checks fail, or the target is unhealthy after rollout.

## Minimum Rollback Packet

- failing deploy target
- last known good version, artifact, or commit
- rollback path or owner
- latest failing evidence
- operator impact and urgency

## Immediate Rules

- If a user-facing flow is broken after deploy, prefer the rollback path over blind retries.
- If rollback is unavailable, state that explicitly as a blocker.
- If the rollback itself is risky, say why before proceeding.

## Hand-Off Language

When rollback is needed, report:

- what failed
- what evidence proves it failed
- what rollback path is available
- whether rollback was executed, deferred, or blocked
- whether the next skill is `forge-systematic-debugging`

## Public Surface Rule

Rollback stays guidance inside the deploy workflow.

Do not advertise `rollback` as a standalone public operator action or slash command.
