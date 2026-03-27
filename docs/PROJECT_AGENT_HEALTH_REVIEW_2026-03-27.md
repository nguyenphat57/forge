# Project Agent Health Review 2026-03-27

## Scope

- Whole monorepo static review with one safe structural refactor in the route-planning core.
- Focused on redundancy, maintainability weak points, and factors that reduce agent performance or routing quality.
- Avoided files already dirty in the workspace before this pass.

## Evidence

- Baseline before refactor: `python scripts/verify_repo.py` -> PASS.
- Targeted verification after refactor: `python -m unittest discover -s packages/forge-core/tests -p 'test_route*.py' -v` -> PASS (12 tests).
- Final verification after all changes: `python scripts/verify_repo.py` -> PASS.

## Findings

1. [Medium] Registry data is still duplicated almost verbatim across core and both adapters, which increases drift risk and expands the reasoning surface for the agent.
   - `packages/forge-core/data/orchestrator-registry.json`: 874 lines.
   - `packages/forge-antigravity/overlay/data/orchestrator-registry.json`: 874 lines.
   - `packages/forge-codex/overlay/data/orchestrator-registry.json`: 869 lines.
   - Similarity to core: antigravity `0.9998`, codex `0.9954`.
   - Impact: every routing or quality-profile change must be kept aligned in three places, and a reader has to inspect multiple near-identical sources to know which one is canonical.
   - Recommendation: keep one canonical registry in core and generate adapter overlays from a small patch file or build-time projection.

2. [Medium] Several central scripts remain monolithic and exceed the repo's preferred file size, so future changes will stay expensive to reason about and risky to review.
   - `packages/forge-core/scripts/run_smoke_matrix.py`: 706 lines.
   - `packages/forge-core/scripts/preferences.py`: 548 lines.
   - `scripts/install_bundle.py`: 497 lines.
   - `packages/forge-core/scripts/prepare_bump.py`: 403 lines.
   - `packages/forge-core/scripts/compat.py`: 356 lines.
   - `packages/forge-core/scripts/response_contract.py`: 347 lines.
   - `packages/forge-core/scripts/run_workspace_canary.py`: 319 lines.
   - `packages/forge-core/scripts/generate_ui_brief.py`: 301 lines.
   - Impact: these files mix parsing, policy, formatting, and orchestration in the same unit, which increases bug density, slows review, and makes agent edits more likely to overshoot scope.
   - Recommendation: continue the support-module extraction pattern used in this pass, starting with `run_smoke_matrix.py` and `preferences.py`.

3. [Medium] Workspace artefacts are large enough to pollute search results and increase accidental context loading for agents.
   - `.install-backups/`: 11,723 files, 56,272,743 bytes.
   - `dist/`: 639 files, 3,769,955 bytes.
   - Impact: repo-wide search and manifest scans can surface generated or backup content before source-of-truth files, which wastes tokens and increases the chance of editing the wrong place.
   - Recommendation: move install backups outside the repo root, or add a small cleanup/rotation command and stricter search excludes in maintainer workflows.

4. [Low] Test code has started to mirror production bloat, which will make future refactors slower even when behavior remains stable.
   - `packages/forge-core/tests/test_preferences.py`: 508 lines.
   - `tests/test_release_repo.py`: 401 lines.
   - Impact: the proof harness is strong, but scenario setup is increasingly concentrated in a few large test files.
   - Recommendation: extract table-driven helpers/fixtures the same way runtime support modules are being extracted.

## Refactor Applied In This Pass

- `packages/forge-core/scripts/route_preview.py` was reduced from 839 lines to 219 lines without changing its public CLI or the functions used by tests and canary tooling.
- Extracted modules:
  - `packages/forge-core/scripts/route_analysis.py` (230 lines)
  - `packages/forge-core/scripts/route_delegation.py` (203 lines)
  - `packages/forge-core/scripts/route_risk.py` (126 lines)
  - `packages/forge-core/scripts/route_local_companions.py` (95 lines)
- Result: route planning now has cleaner responsibility boundaries for intent/complexity analysis, risk heuristics, delegation planning, and local companion resolution.

## Assumptions And Gaps

- No runtime latency benchmark exists for route preview, so performance conclusions are based on code size, duplication, artefact volume, and search noise rather than micro-benchmark numbers.
- This pass intentionally did not modify files that were already dirty in the workspace, especially around release/install support.

## Disposition

- `changes-required`

## Finish Branch

- `continue-on-branch`

## Summary

- The route-planning core is materially healthier after this refactor and remains fully verified.
- The next highest-value work is to canonicalize registry ownership and continue splitting the remaining large orchestration scripts.
