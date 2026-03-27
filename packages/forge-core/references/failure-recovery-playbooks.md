# Forge Failure-Recovery Playbooks

> Use this when the chain is stuck, a gate is blocked, or deploy/review/session work cannot continue safely without a reset.

## Debug Stall

Use when:
- 2-3 consecutive hypotheses fail
- 3 fix attempts fail
- reproduction is unstable

Do this now:
1. Stop patching.
2. Record the eliminated hypotheses.
3. Reclassify the problem as `code`, `data`, or `environment`.
4. If the boundary or system shape is still ambiguous, route back to `plan` or `architect`.

Desired outcome:
- a stronger new hypothesis, or
- a clear escalation to `plan` or `architect`

## Quality Gate Blocked

Use when:
- the quality gate returned `blocked`
- there is not enough evidence to claim done or release readiness

Do this now:
1. Name the first gate that failed.
2. List the missing evidence precisely.
3. Choose the shortest path that can produce that evidence.
4. If the claim is too broad, narrow the claim instead of trying to bypass the gate.

Desired outcome:
- a gate retry with fresh evidence, or
- a smaller but accurate claim/disposition

## Deploy Failed Or Smoke Failed

Use when:
- the deploy command failed
- post-deploy smoke checks failed
- identity or target checks show the wrong environment

Do this now:
1. Stop the rollout.
2. Pin the release ID, target, and affected scope.
3. If a user-facing flow is failing, activate the rollback path immediately.
4. Collect logs and output from the exact failure point.
5. Route to `debug` after the service returns to a safe state.

Desired outcome:
- the service returns to a safe state before deeper investigation continues

## Review Deadlock

Use when:
- feedback loops without converging
- reviewer and implementer are arguing from instinct instead of evidence

Do this now:
1. Classify each feedback item using the feedback response matrix.
2. Separate technical fact, convention, and ownership decision.
3. If the disagreement is factual, get evidence.
4. If it is a policy or convention question, let the owner decide.

Desired outcome:
- fix, challenge with evidence, or ask one clarifying question

## Continuity Mismatch

Use when:
- `.brain` says one thing and repo state says another
- an old handover no longer matches the current branch or task

Do this now:
1. Let repo state win.
2. Drop memory that no longer matches the current scope.
3. Capture a fresh decision or learning artifact if needed.
4. Do not try to merge incompatible memories.

Desired outcome:
- clean, scope-filtered context without stale assumptions
