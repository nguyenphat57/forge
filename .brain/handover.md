HANDOVER
- Current task: Cut `1.15.0` and mark it as the current stable Forge release after shipping host-aware delegation preference.
- Done: Updated `VERSION`, `CHANGELOG.md`, spec doc, and `.brain` continuity (`decisions`, `learnings`, `session`, `handover`) for `1.15.0`.
- Done: Host capability resolution now uses `default_tier` in core, Codex overlays `parallel-workers`, and Antigravity degrades honestly to `controller-baseline`.
- Done: Typed `delegation_preference` now resolves through bootstrap, route preview, runtime routing, and legacy `custom_rules` compatibility.
- Remaining: none for this release slice.
- Important decisions: Keep delegation automation tied to canonical typed preference plus host capability, not prose-only `custom_rules`.
- Verification run: `python packages/forge-core/scripts/run_smoke_matrix.py` -> PASS (49/49), `python scripts/build_release.py --format json` -> PASS, `python scripts/verify_repo.py --format json` -> PASS.
- Next step: Optional only, if requested, create a Git tag or GitHub Release note for `1.15.0`.
