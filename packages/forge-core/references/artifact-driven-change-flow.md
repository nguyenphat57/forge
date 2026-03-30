# Artifact-Driven Change Flow

Use this flow for `medium` or risky build work where Forge should carry durable artifacts from clarification through gate.

## Goal

Run a change with:
- explicit requirements quality check
- packet readiness check
- isolated baseline proof
- persisted change verification
- quality gate backed by artifacts

## Recommended Sequence

1. Start the active change packet.

```powershell
python scripts/change_artifacts.py start "Add checkout retry" --workspace C:\path\to\workspace --task "Implement retry guard in checkout flow" --verification "pytest tests/test_checkout.py -k retry"
```

2. Run a lightweight requirements checklist.

```powershell
python scripts/generate_requirements_checklist.py --requirement "Checkout retry must recover failed payments within 3 attempts and verify with a repeatable checkout scenario."
```

If this warns, sharpen the requirement before planning more.

3. Check the implementation packet before build.

```powershell
python scripts/check_spec_packet.py --source .forge-artifacts\changes\active\add-checkout-retry\implementation-packet.md --source .forge-artifacts\changes\active\add-checkout-retry\specs\add-checkout-retry\spec.md
```

If this fails or warns, ask one decisive clarification question and reopen upstream instead of improvising.

4. Prepare an isolated worktree and baseline proof.

```powershell
python scripts/prepare_worktree.py --workspace C:\path\to\workspace --name checkout-retry --baseline-command "python -m pytest tests/test_checkout.py -k retry" --persist
```

5. Implement the first slice and update change status with fresh proof.

```powershell
python scripts/change_artifacts.py status --workspace C:\path\to\workspace --slug add-checkout-retry --state ready-for-review --note "First retry slice is implemented." --verified "pytest tests/test_checkout.py -k retry"
```

6. Verify the change packet itself.

```powershell
python scripts/verify_change.py --workspace C:\path\to\workspace --slug add-checkout-retry --persist
```

Expected result:
- `PASS` means artifacts, proof, and spec delta are aligned enough for downstream claims.
- `WARN` means revise before stronger claims.
- `FAIL` means the packet is not safe to hand off.

7. Record the quality gate from fresh evidence.

```powershell
python scripts/record_quality_gate.py --workspace C:\path\to\workspace --project-name "Checkout Retry" --profile standard --target-claim ready-for-review --decision go --evidence "pytest tests/test_checkout.py -k retry" --response "I verified: checkout retry proof passed." --why "The first slice is bounded and the change packet is aligned." --persist
```

8. After review/merge, archive the change.

```powershell
python scripts/change_artifacts.py archive --workspace C:\path\to\workspace --slug add-checkout-retry --decision "Merged after review" --learning "Retry boundary stays inside checkout service"
```

## Minimal Evidence Rule

Do not jump from implementation to `done` or `deploy` just because tests passed.

For medium/risky work, the stronger path is:
- proof of the slice
- updated change packet
- `verify-change`
- `quality-gate`

## Files You Should Expect

- `.forge-artifacts/changes/active/<slug>/proposal.md`
- `.forge-artifacts/changes/active/<slug>/design.md`
- `.forge-artifacts/changes/active/<slug>/implementation-packet.md`
- `.forge-artifacts/changes/active/<slug>/tasks.md`
- `.forge-artifacts/changes/active/<slug>/verification.md`
- `.forge-artifacts/changes/active/<slug>/resume.md`
- `.forge-artifacts/changes/active/<slug>/specs/<slug>/spec.md`
- `.forge-artifacts/verify-change/<slug>/`
- `.forge-artifacts/quality-gates/<project-slug>/`
- `.forge-artifacts/worktree-prep/<worktree-slug>/`
