HANDOVER
- Current task: Cut `1.15.1` as a bounded maintenance release and keep stable-release surfaces plus continuity artifacts aligned.
- Done: Updated all `forge-core` child skills so the closing footer line reads `Used skill: <skill-name>.` and multi-skill footer blocks do not repeat duplicate skill lines.
- Done: Refreshed `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/public-readiness.md`, and `docs/release/release-process.md` so `1.15.1` is the current stable maintenance release.
- Done: Updated `.brain/decisions.json`, `.brain/learnings.json`, `.brain/session.json`, and this handover so the current stable line, release reasoning, and footer-provenance learning all match `1.15.1`.
- Remaining: none for this maintenance patch after bundle sync and install sync complete.
- Important decisions: Keep the release on the `1.15.x` maintenance line as a patch; use neutral `Used skill:` footer wording and emit each used skill only once.
- Verification run: `python scripts/verify_repo.py` -> PASS, `python scripts/build_release.py` -> PASS.
- Next step: Optional only, if requested, continue bounded maintenance work or reopen the roadmap only when target-state reopen criteria are met.
