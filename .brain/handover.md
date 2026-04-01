HANDOVER
- Current task: Prepare the 1.11.0 minor release for the 1.11.x hardening roadmap.
- Done: Hardened secret scan, dirty-tree release provenance, solo-profile and release-tail docs, materialized overlay contract checks, route-preview workflow-state round-tripping, and bumped `VERSION` plus `CHANGELOG.md` to `1.11.0`.
- Remaining: none.
- Important decisions: Treat fresh dist-bundle verification and workflow-state round-tripping as release-blocking contracts before shipping `1.11.0`.
- Verification run: `PYTHONPATH='packages/forge-core/scripts;packages/forge-core/tests' python -m unittest packages/forge-core/tests/test_help_next_workflow_state.py packages/forge-core/tests/test_tool_roundtrip.py packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_route_preview.py -v` -> PASS; `PYTHONPATH='tests' python -m unittest tests.test_secret_scan tests.release_repo_test_contracts tests.release_repo_test_overlays -v` -> PASS; `python scripts/verify_repo.py` -> PASS.
- Next step: Continue from `1.11.0` only if a post-release rollout note or follow-up hardening slice is needed.
