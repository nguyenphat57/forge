# Forge Monorepo Architecture

## Goal

Keep one canonical implementation of Forge while supporting multiple host surfaces.

Boundary reference: see `docs/architecture/adapter-boundary.md`.

## Source of Truth vs Build Artifacts

- `packages/` is the development source of truth.
- Each adapter package keeps its overlay under `packages/<adapter>/overlay/`.
- `dist/` is generated release output built from `forge-core` plus one adapter overlay.
- Do not treat `dist/` as an independent source tree; fixes belong in `packages/` and are verified again after rebuild.

## Package Roles

### `forge-core`

Canonical source-of-truth for:

- orchestrator registry
- routing logic
- verification and canary scripts
- shared workflows, domains, and references
- tests

`forge-core` should not depend on a single host-specific entry file.

### `forge-antigravity`

Adapter overlay for Antigravity:

- host-specific `SKILL.md`
- `agents/openai.yaml`
- 10 operator wrapper workflows for `help`, `next`, `run`, `bump`, `rollback`, `customize`, `init`, `recap`, `save-brain`, and `handover`
- one adapter data compatibility file: `data/preferences-compat.json`
- one adapter reference: `references/antigravity-operator-surface.md`
- Antigravity-oriented host boundary wording

### `forge-codex`

Adapter overlay for Codex:

- Codex-specific `SKILL.md`
- `AGENTS.example.md` for workspace integration
- `AGENTS.global.md` for global Codex host takeover
- 2 execution-layer additions: `workflows/execution/dispatch-subagents.md` and a Codex-specific `session.md`
- 7 thin operator wrappers for `help`, `next`, `run`, `bump`, `rollback`, `customize`, and `init`
- 3 adapter references: `codex-operator-surface.md`, `smoke-test-checklist.md`, `smoke-tests.md`
- one adapter data override: `data/orchestrator-registry.json`
- one adapter script: `scripts/enable_windows_utf8.ps1`
- Codex-oriented host boundary wording

## Adapter Surface Differences

- Antigravity keeps dedicated session ergonomics aliases such as `/recap`, `/save-brain`, and `/handover`.
- Codex does not mirror those legacy wrappers; it keeps a thinner operator surface and adds native multi-agent dispatch instead.
- This is an intentional adapter-level UX difference, not a parity bug in `forge-core`.

## Release Flow

1. Start from `packages/forge-core`.
2. Copy core into `dist/forge-core`.
3. Copy core into each adapter bundle under `dist/`.
4. Overlay adapter files on top of the copied core.
5. Run verify on the built bundles.
6. Install from `dist/` into runtime paths with `scripts/install_bundle.py`.

This avoids three drifting copies of the same logic.

## Rules

- Routing logic changes belong in `forge-core`.
- Host entry files and adapter UX wrappers belong in adapters.
- Shared tests belong in `forge-core`.
- Installed bundles under `dist/` are release artifacts, not development source.
- Canonical version lives in `/VERSION`, not in installed runtimes.
- `forge-core` must stay clean enough for future adapters such as `forge-claude`.
- If a feature is host-shaped, keep the engine in core only when it is truly reusable, and keep the wrapper in the adapter.
