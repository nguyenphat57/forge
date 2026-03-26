# Forge Failure Recovery Playbooks

> Used when the chain is stuck, the gate is blocked, or the deploy/review/session enters a state where it cannot continue safely if improvised.

## Debug Stalled

When to use:
- 2-3 consecutive hypotheses are not confirmed
- 3 fix attempts fail
- Reproduction is unstable

Do it now:
1. Stop further patching.
2. Record the eliminated hypotheses.
3. Select lens again: `code`, `data`, or `environment`.
4. If the boundary/system shape is ambiguous, route to `plan` or `architect`.

Desired results:
- There is a new, better hypothesis, or
- There is clear escalation to `plan`/`architect`

## Quality Gate Blocked

When to use:
- Quality gate ra `blocked`
- Not enough evidence to claim done/release

Do it now:
1. Indicates the first gate failed.
2. List the correct missing evidence.
3. Choose the shortest path to get that evidence.
4. If the current claim is too big, lower the claim instead of trying to bypass the gate.

Desired results:
- Gate retry with new evidence, or
- Claim/disposition is smaller but correct

## Deploy Failed Or Smoke Failed

When to use:
- Deploy command fail
- Post-deploy smoke fail
- Identity/target check detected the wrong environment

Do it now:
1. Stop the rollout.
2. Pin release id, target, and scope of influence.
3. If the main user-facing flow fails, enable rollback path immediately.
4. Collect log/output at the correct failure point.
5. Route to `debug` after the service is returned to a safe state.

Desired results:
- Service returns to a safe state, then investigate deeply

## Review Deadlock

When to use:
- Feedback goes back and forth but does not converge
- Reviewer and implementer are arguing by feeling

Do it now:
1. Attach each feedback to `feedback response matrix`.
2. Separate clearly: technical fact, convention, or ownership decision.
3. If the dispute is factual, get evidence.
4. If the dispute is a policy/convention, the owner decides.

Desired results:
- Fix, challenge with evidence, or clarify question only

## Continuity Mismatch

When to use:
- `.brain` says one thing, repo state says another
- The old Handover is no longer valid for the current branch/task

Do it now:
1. Repo state wins.
2. Remove memory that no longer matches the current scope.
3. Recapture the correct decision/learning with a new artifact if necessary.
4. Don't try to "reconcile" by mixing both sources.

Desired results:
- Context is clean, scope-filtered, and does not carry stale assumptions
