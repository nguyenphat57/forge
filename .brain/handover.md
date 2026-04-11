HANDOVER
- Current task: Cut `1.17.0` as the stable release for the workflow slim-down tranche and keep release plus continuity surfaces aligned.
- Done: Retired nine low-value Forge workflows from the live core surface: `change`, `verify-change`, `review-pack`, `release-doc-sync`, `release-readiness`, `adoption-check`, `doctor`, `dashboard`, and `map-codebase`.
- Done: Replaced `doctor -> map-codebase` onboarding with direct `help/next -> plan` guidance and slimmed the default solo release tail to end at `deploy`.
- Done: Refreshed `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/public-readiness.md`, `docs/release/release-process.md`, `.brain/decisions.json`, and `.brain/session.json` so `1.17.0` is the current stable release.
- Done: Built `dist/`, synced `forge-antigravity` and `forge-codex` from the `1.17.0` bundles, and re-applied the Codex UTF-8 helper for Vietnamese output.
- Remaining: none.
- Important decisions: Treat this cut as `1.17.0` on the reopened slim-refactor roadmap line; keep onboarding direct through `help` or `next` instead of reintroducing `doctor` or `map-codebase`.
- Verification run: `python scripts/build_release.py --format json` -> PASS, `python scripts/verify_repo.py` -> PASS, `python scripts/install_bundle.py forge-antigravity --upgrade --activate-gemini --format json` -> PASS, `python scripts/install_bundle.py forge-codex --upgrade --activate-codex --format json` -> PASS, `powershell -ExecutionPolicy Bypass -File "$HOME/.codex/skills/forge-codex/scripts/enable_windows_utf8.ps1" -Persist` -> PASS.
- Next step: If another tranche follows, continue from the slim-refactor roadmap without reintroducing the retired workflow surface.
