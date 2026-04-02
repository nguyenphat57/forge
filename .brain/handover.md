HANDOVER
- Current task: Cut `1.14.0` and mark it as the current stable Forge release after completing the competitive roadmap line.
- Done: Updated `VERSION`, `CHANGELOG.md`, stable-release references, and `.brain` continuity (`decisions`, `learnings`, `session`, `handover`) for `1.14.0`.
- Done: Full roadmap-complete and canonical release gates are green (`pytest` release sweep + `verify_repo.py` + `verify_bundle.py`).
- Done: Runtime tool registrations for both Codex and Gemini state roots were refreshed to the current runtime targets.
- Remaining: none for this release slice.
- Important decisions: Keep `1.14.0` stable status tied to proof from packet/host/runtime contracts, not docs-only claims.
- Verification run: `python -m pytest ... tests/release_repo_test_contracts.py -q` -> PASS, `python scripts/verify_repo.py` -> PASS, `python scripts/verify_bundle.py` -> PASS.
- Next step: Optional only, if Sếp wants to create a Git tag/GitHub Release note for `1.14.0`.
