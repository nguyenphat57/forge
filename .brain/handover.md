HANDOVER
- Current task: Cut `1.16.0` as the stable release for the domain-skill retirement tranche and keep release plus continuity surfaces aligned.
- Done: Retired `frontend` and `backend` as surfaced Forge domain skills by removing `domain_skills` from routing, route preview output, activation lines, canary checks, and smoke validators.
- Done: Absorbed the useful backend and UI guidance into `build`, `spec-review`, `visualize`, and the reference map while keeping the backend or UI brief tooling available as workflow-support tooling.
- Done: Refreshed `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/public-readiness.md`, `docs/release/release-process.md`, `.brain/decisions.json`, and `.brain/session.json` so `1.16.0` is the current stable release.
- Done: Built `dist/`, synced `forge-antigravity` and `forge-codex` from the `1.16.0` bundles, and re-applied the Codex UTF-8 helper for Vietnamese output.
- Remaining: none.
- Important decisions: Treat this cut as `1.16.0` on the reopened slim-refactor roadmap line; keep UI heuristics internal-only instead of preserving `frontend` or `backend` as first-class skills.
- Verification run: `python scripts/build_release.py --format json` -> PASS, `python scripts/verify_repo.py --profile fast` -> PASS, `python scripts/install_bundle.py forge-antigravity --upgrade --activate-gemini --format json` -> PASS, `python scripts/install_bundle.py forge-codex --upgrade --activate-codex --format json` -> PASS.
- Next step: If another tranche follows, continue from the slim-refactor roadmap without reintroducing domain-skill surface area.