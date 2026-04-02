HANDOVER
- Current task: Keep `1.15.x` in maintenance closure and keep continuity artifacts aligned with the current stable Forge release.
- Done: Added `docs/plans/2026-04-02-forge-1.15.x-maintenance-closure.md` and marked older roadmap files under `docs/plans/` as historical or implemented.
- Done: Promoted the `1.15.x` closure target, maintenance boundary, and reopen criteria in tracked references and release-hardening tests.
- Done: Updated `.brain/decisions.json`, `.brain/session.json`, and this handover so `1.12.0`, `1.13.0`, and `1.14.0` read as historical stable slices while `1.15.0` remains the current stable line.
- Remaining: none for this maintenance-closure sync.
- Important decisions: Reopen the roadmap only when target-state reopen criteria are met; otherwise keep changes inside bounded maintenance.
- Verification run: `python -m pytest tests/test_release_hardening.py tests/release_repo_test_contracts.py -q` -> PASS, `python scripts/verify_repo.py` -> PASS.
- Next step: Optional only, if requested, sync future continuity artifacts or cut a new roadmap line when maintenance-boundary evidence says the current contract is no longer enough.
