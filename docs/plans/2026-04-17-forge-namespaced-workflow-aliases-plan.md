# Plan: Forge Namespaced Workflow Aliases

Status: implemented

## Goal

Thêm exact workflow namespace `/forge:<workflow>` cho workflow surface của Forge, giữ alias ngắn cũ làm compatibility layer, và làm cho generated docs với route preview dùng cùng một contract.

## Files In Scope

- `docs/architecture/generated-host-artifacts/AGENTS.global.canonical.md`
- `docs/architecture/generated-host-artifacts/GEMINI.global.canonical.md`
- `scripts/operator_surface_support.py`
- `packages/forge-core/scripts/route_policy.py`
- `packages/forge-core/scripts/route_preview_builder.py`
- `packages/forge-core/tests/test_route_preview.py`
- `tests/test_operator_surface_registry.py`

## Verification First

- Host artifact check: `python scripts/generate_host_artifacts.py --check --format json`
- Route preview tests: `python -m unittest discover -s packages/forge-core/tests -p test_route_preview.py -v`
- Registry/generated doc tests: `python -m unittest discover -s tests -p test_operator_surface_registry.py -v`

## Execution Steps

1. Add RED tests for explicit `/forge:<workflow>` behavior in route preview.
2. Add RED tests for generated host docs showing namespaced aliases and retaining legacy aliases.
3. Implement shared workflow alias extraction/rendering.
4. Implement explicit workflow override in route policy/preview.
5. Regenerate host artifacts.
6. Rerun the same verification commands and report actual outcomes.
