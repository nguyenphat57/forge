# Forge Monorepo Architecture

## Goal

Keep one canonical implementation of Forge while supporting multiple host surfaces.

Boundary reference: see `docs/architecture/adapter-boundary.md`.

## Package roles

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
- Antigravity-oriented host boundary wording

### `forge-codex`

Adapter overlay for Codex:

- Codex-specific `SKILL.md`
- `AGENTS.example.md` for workspace integration
- Codex-oriented host boundary wording

## Release flow

1. Start from `packages/forge-core`.
2. Copy core into `dist/forge-core`.
3. Copy core into each adapter bundle under `dist/`.
4. Overlay adapter files on top of the copied core.
5. Run verify on the built bundles.
6. Install from `dist/` into runtime paths with `scripts/install_bundle.py`.

This avoids three drifting copies of the same logic.

## Rules

- Routing logic changes belong in `forge-core`.
- Host entry files belong in adapters.
- Shared tests belong in `forge-core`.
- Installed bundles are release artifacts, not development source.
- Canonical version lives in `/VERSION`, not in installed runtimes.
- `forge-core` must stay clean enough for future adapters such as `forge-claude`.
- If a feature is host-shaped, keep the engine in core only when it is truly reusable, and keep the wrapper in the adapter.
