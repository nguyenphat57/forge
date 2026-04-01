HANDOVER
- Current task: Prepare the 1.12.0 minor release for the 1.12.x maturation roadmap.
- Done: Froze the canonical four-tier release contract, bounded adoption-check and release follow-up, made `help`/`next`/dashboard read release-tail state, hardened roadmap closure rules, and bumped `VERSION` plus `CHANGELOG.md` to `1.12.0`.
- Remaining: none for the repo release slice.
- Important decisions: Keep `1.12.0` on one canonical four-tier vocabulary and require a separate roadmap-complete sweep before claiming Commits 6 to 10 are also closed.
- Verification run: `python scripts/verify_repo.py` -> PASS; `python scripts/build_release.py --format json` -> PASS; roadmap closure checks -> PASS; implementation-plan alignment checks -> PASS; deferred-boundary rationale checks -> PASS.
- Next step: Refresh installed `.codex` and `.gemini` runtimes from the fresh `dist/` bundles if local host rollout is needed.
