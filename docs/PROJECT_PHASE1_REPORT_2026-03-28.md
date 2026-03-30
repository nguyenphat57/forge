# Phase 1 Implementation Report

Date: 2026-03-28
Status: Completed
Scope:
- doctor
- map-codebase
- change artifacts plus archive loop
- continuity and routing integration needed to make those surfaces usable

Inputs:
- [2026-03-28-forge-solo-dev-roadmap.md](plans/2026-03-28-forge-solo-dev-roadmap.md)
- [2026-03-28-phase-1-build-spec.md](specs/2026-03-28-phase-1-build-spec.md)
- [2026-03-28-phase-1-issue-breakdown.md](specs/2026-03-28-phase-1-issue-breakdown.md)

## Summary

Phase 1 is complete at the repo level.

Forge now has:
- a real `doctor` surface for environment, workspace, and runtime health
- a real `map-codebase` surface for brownfield project mapping
- durable change artifacts for medium and large work
- archive hooks that write back into `.brain/decisions.json` and `.brain/learnings.json`
- `help/next` integration for codebase maps and active changes
- routing support that marks medium and large edit work as requiring change artifacts

This is enough to say Forge is no longer only an orchestration kernel. It now has a usable Phase 1 solo-dev surface before any first-party lane work starts.

## Delivered Work

### 1. `doctor`

New files:
- `packages/forge-core/workflows/operator/doctor.md`
- `packages/forge-core/scripts/doctor.py`
- `packages/forge-core/scripts/doctor_environment.py`
- `packages/forge-core/scripts/doctor_runtime.py`
- `packages/forge-core/scripts/doctor_workspace.py`
- `packages/forge-core/scripts/doctor_report.py`
- `packages/forge-core/tests/test_doctor.py`

Behavior:
- checks Python, git, Node relevance, workspace sanity, preferences readability, bundle registry, artifact write access, runtime tool resolution, and browse runtime health
- persists JSON reports under `.forge-artifacts/doctor/`
- supports `--json` and `--strict`
- treats runtime bundles as optional warnings, not default blockers

### 2. `map-codebase`

New files:
- `packages/forge-core/workflows/operator/map-codebase.md`
- `packages/forge-core/scripts/map_codebase.py`
- `packages/forge-core/scripts/map_codebase_detect.py`
- `packages/forge-core/scripts/map_codebase_structure.py`
- `packages/forge-core/scripts/map_codebase_focus.py`
- `packages/forge-core/scripts/map_codebase_report.py`
- `packages/forge-core/tests/test_map_codebase.py`
- `packages/forge-core/tests/fixtures/workspaces/map_codebase_next_workspace/*`
- `packages/forge-core/tests/fixtures/workspaces/map_codebase_python_workspace/*`

Behavior:
- detects stack from `package.json` or `pyproject.toml`
- writes durable artifacts under `.forge-artifacts/codebase/`
- emits summary, stack, architecture, conventions, testing, integrations, risks, and open questions
- supports focus artifacts such as `focus/frontend.md` or `focus/api.md`

### 3. Change Artifacts And Archive Loop

New files:
- `packages/forge-core/workflows/execution/change.md`
- `packages/forge-core/scripts/change_artifacts.py`
- `packages/forge-core/scripts/change_artifacts_paths.py`
- `packages/forge-core/scripts/change_artifacts_status.py`
- `packages/forge-core/scripts/change_artifacts_archive.py`
- `packages/forge-core/scripts/change_guard.py`
- `packages/forge-core/tests/test_change_artifacts.py`

Behavior:
- `start` creates `proposal.md`, `design.md`, `tasks.md`, `status.json`, `verification.md`
- `status` updates state and verification evidence
- `archive` moves the active change into archive and writes back decisions and learnings
- `guard` classifies risky actions as `allow`, `warn`, or `block`

### 4. Continuity And Routing Integration

Changed files:
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/scripts/resolve_help_next.py`
- `packages/forge-core/scripts/route_analysis.py`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/tests/test_help_next.py`
- `packages/forge-core/tests/test_help_next_workflow_state.py`
- `packages/forge-core/tests/test_route_preview.py`

Behavior:
- `help/next` now recognizes:
  - mapped repos
  - active changes
  - workflow-state summaries
- Forge ignores internal `.forge-artifacts/` noise when reading git status
- route preview now marks medium and large edit work with `change_artifacts_required: true`

## Verification

Primary verification:

```text
python -m pytest packages/forge-core/tests -q
Result: 107 passed, 5 skipped, 189 subtests passed in 12.31s
```

Targeted smoke checks:

```text
python packages/forge-core/scripts/doctor.py --workspace . --format json
Result: WARN
Reason: runtime tool registry path is not configured, but bundle-neighbor runtime resolution and browse health both passed
```

```text
python packages/forge-core/scripts/map_codebase.py --workspace <next fixture> --focus frontend --format json
Result: PASS
Detected: project storefront-app, languages typescript, frameworks nextjs/react/prisma
```

```text
python packages/forge-core/scripts/route_preview.py "Implement a new checkout feature" --changed-files 3 --format json
Result: PASS
Detected: BUILD, medium, change_artifacts_required=true
```

## Phase 1 Exit Criteria Check

- install plus `doctor` is understandable: yes
- brownfield repo mapping works: yes
- continuity is useful in practice: yes, through active change status plus archive back into `.brain`
- medium and large work survives after the chat window: yes
- Forge feels useful before any first-party lane exists: yes

## Residual Risk

- `doctor` currently warns when no runtime registry path is configured, even if bundle-neighbor resolution succeeds. This is acceptable for Phase 1 but can be refined later.
- `map-codebase` detection is intentionally shallow. It is good enough for brownfield onboarding, not for deep semantic understanding.
- `change_guard` only covers an initial keyword-based risk set. It is a first guardrail, not a full policy engine.
- `.tmp/` still exists in workspace because shell-level directory deletion was blocked by policy during cleanup.

## Notable Guardrail Compliance

- all newly added implementation files are under 300 lines
- `test_help_next.py` was split so test files also respect the line-count rule
- docs artifacts for roadmap, audit, spec, and issue breakdown are present and linked

## Bottom Line

Phase 1 is complete for Forge core.

The repo now has a working foundation for:
- environment diagnosis
- brownfield onboarding
- durable medium and large work artifacts
- continuity through active changes and archive-back memory

Phase 2 can now start from a stronger product surface instead of continuing to invest only in extensibility.
