# Project Review 2026-03-27

## Scope

- Whole monorepo static review.
- Executed verification on the current workspace state.
- Focused on release/build, install safety, and security controls.

## Evidence

- `python scripts/verify_repo.py`
- `python -m unittest discover -s tests -v`
- `python packages/forge-core/scripts/verify_bundle.py`
- `python scripts/build_release.py --format json`
- `python scripts/install_bundle.py forge-codex --dry-run --target .tmp\repo-target --format json`
- `python scripts/install_bundle.py forge-antigravity --dry-run --target dist\sandbox-target --format json`
- `python scripts/install_bundle.py forge-codex --dry-run --target packages\sandbox-target --format json`

## Findings

1. [High] Windows release verification is flaky because the release pipeline uses raw destructive filesystem calls with no retry or recovery path.
   - `scripts/build_release.py` deletes bundle directories via `shutil.rmtree()` before every rebuild.
   - `scripts/install_bundle.py` also relies on raw `rmtree()`, `unlink()`, and `copytree()` during sync.
   - On the current workspace, `python scripts/verify_repo.py` failed in `repo.unittest` with `WinError 5`, `WinError 32`, and `WinError 145` while rebuilding `dist/`.
   - Impact: the documented release gate is not dependable on the same `windows-latest` platform used by CI, so a clean source state can still fail verification and block release.
   - Relevant code: `scripts/build_release.py:45-47`, `scripts/build_release.py:122-127`, `scripts/install_bundle.py:338-362`, `scripts/install_bundle.py:469-488`.

2. [Medium] Install target validation does not enforce the safety contract described in the release docs.
   - The docs say not to install into `packages/`, `dist/`, or the repo root.
   - `validate_install_paths()` only rejects the exact root paths, not descendants.
   - Dry-run accepted all of these repo-local targets without error: `.tmp\repo-target`, `dist\sandbox-target`, `packages\sandbox-target`.
   - Impact: a mistaken real install can prune files inside the repo tree because sync mode removes entries not present in the bundle.
   - Relevant code: `scripts/install_bundle.py:72-83`.
   - Relevant docs: `docs/release/install.md:48-55`.

3. [Medium] The release verification path has no repeatable secret scanning step, despite the repo’s own security workflow requiring one for release-grade work.
   - CI only runs `python scripts/verify_repo.py`.
   - A repo-wide grep found no `gitleaks`, `trufflehog`, `git-secrets`, or equivalent automated secret scan in workflow or release scripts.
   - Impact: accidental credential disclosure or wrong-scope secret files can ship without a dedicated gate.
   - Relevant code: `.github/workflows/verify.yml:1-17`.

4. [Low] Overlay builds reintroduce cached artifacts into release bundles.
   - Core copy uses ignore patterns for `__pycache__`, `*.pyc`, and `.pytest_cache`.
   - Overlay application copies every file under the overlay tree without the same filter.
   - Current `dist/forge-antigravity` and `dist/forge-codex` outputs contain adapter `tests/__pycache__` content.
   - Impact: larger and noisier artifacts, plus extra Windows file handles that can worsen rebuild instability.
   - Relevant code: `scripts/build_release.py:16`, `scripts/build_release.py:54-64`.

## Assumptions And Gaps

- This was primarily a static audit with targeted command execution, not a host-level end-to-end rollout on real Codex or Gemini homes.
- I did not run external secret scanners because none are wired into the repo today.
- `packages/forge-core` verifies cleanly in isolation; the breakage is concentrated in the monorepo release/install layer.

## Security Review

- Scope: release/build scripts, install safety, and CI verification controls.
- Secret controls: no repeatable secret scan found in repo automation.
- Identity check: not applicable because no real deployment target was used.
- Critical/High: one high operational finding in the Windows release gate.
- Medium/Low: one medium install-safety finding, one medium security-process finding, one low artifact-hygiene finding.
- Score: 64/100.
- Release decision: blocked until the release gate is stable and secret scanning is added.

## Disposition

- Disposition: `changes-required`
- Finish branch: `continue-on-branch`

## Summary

- `forge-core` itself is in much better shape than the repo wrapper around build/install/release.
- The main blocker is not application logic; it is release reliability and safety on Windows.
- Fixing the filesystem handling and target guardrails should be the first priority before any new rollout.
