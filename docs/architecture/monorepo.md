# Forge Monorepo Architecture

## Goal

Keep one canonical implementation of Forge while supporting multiple host surfaces.

Boundary reference: see `docs/architecture/adapter-boundary.md`.
Bundle-layer ownership reference: see `packages/forge-core/references/architecture-layers.md`.

## Source of Truth vs Build Artifacts

- `packages/` is the development source of truth.
- Each adapter package keeps its overlay under `packages/<adapter>/overlay/`.
- Generated host artifacts stay source-controlled, but their canonical inventory lives in `docs/architecture/host-artifacts-manifest.json` and their canonical text lives beside that manifest, including thin Codex host wrappers that should not drift from their canonical source.
- `dist/` is generated release output built either from `forge-core` plus one adapter overlay, or from a standalone runtime tool package.
- Do not treat `dist/` as an independent source tree; fixes belong in `packages/` and are verified again after rebuild.

## Four-Layer Model

Forge changes should respect four layers:

1. `core`
2. `generated artifacts`
3. `workflow state`
4. `runtime tools`

The canonical layer contract lives in `packages/forge-core/references/architecture-layers.md`.

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

### `forge-browse`

Runtime tool package for browser-side actuation:

- persistent logical browsing sessions
- HTTP control plane for open, snapshot, and assert flows
- bundle-local verify/tests that do not depend on `forge-core`
- runtime-tool state rooted beside the installed bundle

### `forge-design`

Runtime tool package for design review artifacts:

- consumes persisted Forge UI briefs
- renders HTML design packets and optional evidence boards without depending on `forge-core` at runtime
- records render history under a runtime-tool state root
- bundle-local verify/tests that stay isolated from adapter logic

## Adapter Surface Differences

- Antigravity keeps dedicated session ergonomics aliases such as `/recap`, `/save-brain`, and `/handover`.
- Codex does not mirror those legacy wrappers; it keeps a thinner operator surface and adds native multi-agent dispatch instead.
- This is an intentional adapter-level UX difference, not a parity bug in `forge-core`.

## Release Flow

1. Start from `packages/forge-core`.
2. Copy core into `dist/forge-core`.
3. Refresh generated host artifacts from canonical sources before adapter overlays are copied.
4. Copy core into each adapter bundle under `dist/`.
5. Overlay adapter files on top of the copied core.
6. Copy runtime-tool bundles directly from `packages/` into `dist/`.
7. Run verify on the built bundles.
8. Install from `dist/` into runtime paths with `scripts/install_bundle.py`.

This avoids three drifting copies of the same logic.

## Rules

- Routing logic changes belong in `forge-core`.
- Host entry files and adapter UX wrappers belong in adapters.
- Runtime actuators belong in runtime tool packages.
- Shared tests belong in `forge-core`.
- Installed bundles under `dist/` are release artifacts, not development source.
- Canonical version lives in `/VERSION`, not in installed runtimes.
- `forge-core` must stay clean enough for future adapters such as `forge-claude`.
- If a feature is host-shaped, keep the engine in core only when it is truly reusable, and keep the wrapper in the adapter.
