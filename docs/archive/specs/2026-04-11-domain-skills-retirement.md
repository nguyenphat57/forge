# Domain Skills Retirement Note

Status: historical
Date: 2026-04-11

## Decision

Forge retired `frontend` and `backend` as first-class domain skills.

The router no longer surfaces domain skills in route previews, activation lines, canary expectations, or skill registries. Any UI heuristics that remain are internal-only routing signals.

## Where The Guidance Moved

- Backend implementation guardrails now live in `packages/forge-core/workflows/execution/build.md`.
- Backend boundary/readiness checks now live in `packages/forge-core/workflows/design/spec-review.md`.
- UI design integrity rules now live in `packages/forge-core/workflows/design/visualize.md`.
- UI implementation guardrails now live in `packages/forge-core/workflows/execution/build.md`.
- Backend/UI first-artifact tooling remains documented in:
  - `packages/forge-core/references/backend-briefs.md`
  - `packages/forge-core/references/ui-briefs.md`
  - `packages/forge-core/references/tooling.md`

## What Stayed Supported

- `scripts/generate_backend_brief.py`
- `scripts/check_backend_brief.py`
- `scripts/generate_ui_brief.py`
- `scripts/check_ui_brief.py`
- `scripts/track_ui_progress.py`

These tools remain part of Forge's supported workflow surface. The retirement only removed the domain-skill layer and its public routing/output surface.
