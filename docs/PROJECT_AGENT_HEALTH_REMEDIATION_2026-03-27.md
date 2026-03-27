# Project Agent Health Remediation 2026-03-27

## Scope

- Phase 2 through final cleanup remediation for agent-health findings.
- Addressed `registry` duplication across adapters, split the central personalization module, decomposed the smoke-matrix runner, installer orchestration, bump preparation, compatibility translation, response-contract validation, UI brief generation, workspace canary execution, and the last oversized test suites.
- Kept existing runtime behavior and release outputs stable.

## Evidence

- `python -m unittest discover -s packages/forge-core/tests -p 'test_preferences.py' -v` -> PASS.
- `python -m unittest discover -s packages/forge-core/tests -p 'test_write_preferences.py' -v` -> PASS.
- `python packages/forge-core/scripts/run_smoke_matrix.py` -> PASS (`43/43`).
- `python -m unittest discover -s packages/forge-core/tests -p 'test_*matrix.py' -v` -> PASS.
- `python -m unittest tests.test_install_bundle_codex_host tests.test_install_bundle_antigravity_host tests.test_release_repo tests.test_release_hardening -v` -> PASS (`25` tests).
- `python -m unittest tests.test_release_repo tests.test_install_bundle_codex_host tests.test_install_bundle_antigravity_host -v` -> PASS.
- `python -m unittest discover -s packages/forge-core/tests -p 'test_bump_workflow.py' -v` -> PASS.
- `python -m unittest discover -s packages/forge-core/tests -p 'test_response_contract.py' -v` -> PASS.
- `python -m unittest discover -s packages/forge-core/tests -p 'test_tool_roundtrip.py' -v` -> PASS.
- `python -m unittest discover -s packages/forge-core/tests -p 'test_workspace_canary.py' -v` -> PASS.
- `python -m unittest tests.test_release_repo -v` -> PASS (`13` tests).
- Source-tree scan excluding `dist/` and `.install-backups/` returns no Python files over `300` lines.
- `python scripts/verify_repo.py` -> PASS.

## Changes Applied

### 1. Registry duplication cut from source overlays

- `packages/forge-antigravity/overlay/data/orchestrator-registry.json` reduced from `874` lines to `12` lines.
- `packages/forge-codex/overlay/data/orchestrator-registry.json` reduced from `869` lines to `17` lines.
- Added build-time materialization helper at `scripts/release_registry.py`.
- `scripts/build_release.py` now merges adapter registry patches onto the canonical core registry when building `dist/`.

Result:

- Source overlays no longer keep near-full copies of the core routing registry.
- Built bundles still ship a complete `data/orchestrator-registry.json`, so runtime behavior and existing release tests remain unchanged.

### 2. Preferences module decomposed into smaller units

- `packages/forge-core/scripts/preferences.py` reduced from `548` lines to `30` lines.
- Extracted:
  - `packages/forge-core/scripts/preferences_paths.py` (`126` lines)
  - `packages/forge-core/scripts/preferences_contract.py` (`180` lines)
  - `packages/forge-core/scripts/preferences_store.py` (`255` lines)

Result:

- Path/state resolution, schema/contract normalization, and load-write behavior now live in separate modules.
- `common.py` and the existing CLI/test surface still consume the same top-level `preferences` API.

### 3. Smoke matrix runner decomposed into focused modules

- `packages/forge-core/scripts/run_smoke_matrix.py` reduced to `30` lines.
- Extracted:
  - `packages/forge-core/scripts/smoke_matrix_cases.py` (`23` lines)
  - `packages/forge-core/scripts/smoke_matrix_runtime.py` (`68` lines)
  - `packages/forge-core/scripts/smoke_matrix_suites.py` (`276` lines)
  - `packages/forge-core/scripts/smoke_matrix_validators.py` (`147` lines)
  - `packages/forge-core/scripts/smoke_matrix_validators_tail.py` (`63` lines)

Result:

- Case definitions, process execution, suite orchestration, and validation helpers are now separated.
- The smoke CLI entrypoint stays stable, and the full repo verification still exercises the rebuilt path through both source and built bundles.

### 4. Install bundle orchestration decomposed into focused modules

- `scripts/install_bundle.py` reduced from `497` lines to `128` lines.
- Extracted:
  - `scripts/install_bundle_paths.py` (`86` lines)
  - `scripts/install_bundle_host.py` (`207` lines)
  - `scripts/install_bundle_runtime.py` (`212` lines)

Result:

- Bundle source checks, host activation rendering, install execution, and manifest formatting now live in separate modules.
- The public `install_bundle.py` API and CLI stay intact, so release tests and host-activation flows continue to hit the same surface.

### 5. Remaining large core scripts split to finish the source cleanup

- `packages/forge-core/scripts/prepare_bump.py` reduced from `403` lines to `54` lines.
- Extracted:
  - `packages/forge-core/scripts/prepare_bump_git.py` (`234` lines)
  - `packages/forge-core/scripts/prepare_bump_report.py` (`99` lines)
  - `packages/forge-core/scripts/prepare_bump_semver.py` (`46` lines)
- `packages/forge-core/scripts/compat.py` reduced from `356` lines to `63` lines.
- Extracted:
  - `packages/forge-core/scripts/compat_paths.py` (`123` lines)
  - `packages/forge-core/scripts/compat_translation.py` (`118` lines)
  - `packages/forge-core/scripts/compat_serialize.py` (`141` lines)
- `packages/forge-core/scripts/response_contract.py` reduced from `347` lines to `71` lines.
- Extracted:
  - `packages/forge-core/scripts/response_contract_text.py` (`31` lines)
  - `packages/forge-core/scripts/response_contract_evidence.py` (`136` lines)
  - `packages/forge-core/scripts/response_contract_locale.py` (`135` lines)

Result:

- Bump inference, compat payload handling, and response-contract validation now each have explicit submodules by concern.
- Existing callers still import the same top-level script names, so bundle/test surfaces remain stable.

### 6. Final oversized helpers and test hotspots removed

- `packages/forge-core/scripts/generate_ui_brief.py` reduced from `301` lines to `43` lines.
- Extracted:
  - `packages/forge-core/scripts/generate_ui_brief_profiles.py` (`147` lines)
  - `packages/forge-core/scripts/generate_ui_brief_render.py` (`100` lines)
- `packages/forge-core/scripts/run_workspace_canary.py` reduced from `319` lines to `41` lines.
- Extracted:
  - `packages/forge-core/scripts/run_workspace_canary_core.py` (`223` lines)
  - `packages/forge-core/scripts/run_workspace_canary_persist.py` (`71` lines)
- `packages/forge-core/tests/test_preferences.py` reduced from `508` lines to `7` lines via wrapper + split suites.
- `tests/test_release_repo.py` reduced from `401` lines to `13` lines via wrapper + split suites.
- Added root `.ignore` to exclude `dist/`, `.install-backups/`, `.forge-artifacts/`, and Python caches from repo-wide search.

Result:

- No Python source or test files outside generated/backup trees remain above the `300`-line threshold.
- Agent search now has a dedicated ignore surface separate from `.gitignore`, which reduces context noise without changing release contents.

## Findings Closed

1. Source-level registry duplication between core and adapter overlays is materially reduced.
2. The monolithic `preferences.py` hotspot is removed.
3. The monolithic `run_smoke_matrix.py` hotspot is removed.
4. The monolithic `install_bundle.py` hotspot is removed.
5. The remaining large core scripts (`prepare_bump.py`, `compat.py`, `response_contract.py`) are removed as hotspots.
6. The remaining borderline-large helper scripts (`generate_ui_brief.py`, `run_workspace_canary.py`) are removed as hotspots.
7. The remaining large test files are split into thematic suites.
8. Search noise from generated and backup artefacts is reduced with a dedicated `.ignore`.

## Remaining Open Findings

- None in the previously tracked agent-health scope.

## Summary

- The tracked refactor backlog is clean on the current workspace state.
- Source-tree scan plus full `verify_repo.py` confirm the repo is back under the intended file-size boundary outside generated and backup trees, with search-noise controls in place for agent work.
