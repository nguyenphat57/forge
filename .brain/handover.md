HANDOVER
- Current task: Mark `1.12.0` as the current stable Forge release in repo-facing docs and continuity state.
- Done: Updated `CHANGELOG.md`, `README.md`, `docs/release/public-readiness.md`, and `docs/release/release-process.md` so they explicitly treat `1.12.0` as stable after the release and roadmap-complete gates passed.
- Remaining: none for the repo release slice.
- Important decisions: Keep `1.12.0` on one canonical four-tier vocabulary, and treat it as stable only because both the canonical release gate and the roadmap-complete sweep are green.
- Verification run: `python -m pytest tests/test_release_hardening.py tests/release_repo_test_contracts.py -q` -> `26 passed, 82 subtests passed`; stable release content checks -> PASS.
- Next step: Optional only, if Sếp muốn sync local release messaging into a Git tag or GitHub release body.
