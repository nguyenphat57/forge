HANDOVER
- Current task: Keep release and continuity surfaces aligned to the `2.3.2` stable line when future edits touch release-facing text or repo-state guidance.
- Done: The older `1.17.0` slim-refactor handoff is historical; the current stable line in repo-facing docs is `2.3.2`.
- Done: `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/public-readiness.md`, `docs/release/release-process.md`, and `.brain/decisions.json` agree on `2.3.2`.
- Remaining: Do not revive superseded `1.17.0` release notes in `.brain/handover.md` or other continuity surfaces.
- Important decisions: Use `docs/plans/forge_refactor_V3.md` as the active roadmap and treat older slim-refactor notes as historical context only.
- Verification run: `python scripts/verify_repo.py` -> PASS on 2026-04-13.
- Next step: If a new tranche starts, route from current repo state and `docs/plans/forge_refactor_V3.md` instead of reusing superseded handoff text.
