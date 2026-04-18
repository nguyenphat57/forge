HANDOVER
- Current task: Keep release and continuity surfaces aligned to the `2.8.0` stable line when future edits touch release-facing text, installed workflow shortcuts, or repo-state guidance.
- Done: The older `1.17.0` slim-refactor handoff is historical; the current stable line in repo-facing docs is `2.8.0`.
- Done: `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/public-readiness.md`, `docs/release/release-process.md`, and `.brain/decisions.json` agree on `2.8.0`.
- Remaining: Do not revive superseded `1.17.0` release notes in `.brain/handover.md` or other continuity surfaces.
- Important decisions: Treat `docs/current/*` plus `packages/forge-core/references/target-state.md` as the live maintainer source of truth and keep roadmap files historical unless reopen criteria are met.
- Verification run: `python scripts/verify_repo.py` -> PASS on 2026-04-18.
- Next step: If a new tranche starts, route from current repo state, `docs/current/*`, and `packages/forge-core/references/target-state.md` instead of reusing superseded roadmap text.
