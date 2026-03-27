# Project Remediation 2026-03-27

## Scope

- Fix all findings from the 2026-03-27 repo audit.
- Validate by root tests, bundle verification, build, install dry-run, and repo verification.

## Findings Closed

### 1. Windows release/build instability

Root cause:

- Raw filesystem operations in release/install flow relied on bare `shutil.rmtree()`, `unlink()`, and `copytree()` with no retry strategy.
- Windows file-handle churn around `dist/` made rebuilds flaky.

Fix:

- Added shared retrying filesystem helper at `scripts/release_fs.py`.
- `scripts/build_release.py` now uses retry-aware delete/copy operations.
- `scripts/install_bundle.py` now uses the same retry-aware filesystem path for backup, sync, and removals.

Result:

- Repeated root builds and post-dist verification rebuilds pass.
- `python scripts/verify_repo.py` now passes cleanly on the current Windows workspace.

### 2. Unsafe install target validation

Root cause:

- Install validation only blocked the exact repo root, `dist`, and `packages` paths.
- Repo-local descendants were still accepted.

Fix:

- `scripts/install_bundle.py` now rejects any install target inside the repo tree.
- `docs/release/install.md` was updated to match the stricter behavior.

Result:

- Dry-run to repo-local targets is now blocked by code instead of relying on operator caution.

### 3. Missing repeatable secret-scan gate

Root cause:

- CI only delegated to `scripts/verify_repo.py`, and that pipeline did not include a secret scan.

Fix:

- Added `scripts/scan_repo_secrets.py`.
- Added `repo.secret_scan` to `scripts/verify_repo.py`.
- Updated `.github/workflows/verify.yml` step label to reflect that the monorepo verify job now includes secret scanning.
- Updated `docs/release/release-process.md` to state that the release gate includes secret scan.

Result:

- Secret scan is now a repeatable, enforced verification step for repo-level release checks.

### 4. Overlay copy leaking cached artifacts into dist bundles

Root cause:

- Core bundle copy filtered `__pycache__`, `.pyc`, and `.pytest_cache`, but overlay copy accepted everything.

Fix:

- Overlay copy in `scripts/build_release.py` now skips ignored cache artifacts using the same filter policy as the core bundle path.

Result:

- `dist/forge-antigravity` and `dist/forge-codex` no longer ship adapter cache artifacts.

## Tests Added

- `tests/test_release_hardening.py`
  - verifies cached Python artifacts are excluded from built bundles
  - verifies repo-local install targets are rejected
  - verifies rebuild stability after executing a dist bundle
  - verifies the repo verify pipeline includes secret scan
- `tests/test_secret_scan.py`
  - verifies the scan passes on a clean workspace
  - verifies the scan fails on a high-signal secret pattern

## Verification Evidence

- `python -m unittest discover -s tests -v`
- `python scripts/verify_repo.py`

Observed status:

- Root unittest suite: PASS
- Repo secret scan: PASS
- Root verify pipeline: PASS
- Dist bundle verification for `forge-antigravity`: PASS
- Dist bundle verification for `forge-codex`: PASS

## Residual Risk

- The secret scan is intentionally high-signal and conservative; it is not a full entropy-based DLP scanner.
- If stricter org policy is required later, the next step should be wiring in a dedicated scanner such as `gitleaks` in addition to the current native gate.
