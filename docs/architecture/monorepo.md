# Forge Monorepo Architecture

## Goal

Keep one canonical implementation of Forge while supporting multiple host surfaces without leaving retired runtime-era packages on the active maintainer path.

Boundary reference: see `docs/architecture/adapter-boundary.md`.
Bundle-layer ownership reference: see `docs/architecture/architecture-layers.md`.

## Source Of Truth vs Build Artifacts

- `packages/forge-core`, `packages/forge-skills`, `packages/forge-codex`, and `packages/forge-antigravity` are the active source-of-truth packages.
- Generated host artifacts stay source-controlled, but their canonical inventory lives in `docs/architecture/host-artifacts-manifest.json`.
- `dist/` is generated release output built from `forge-core`, one active adapter overlay, and the sibling Forge skill pack.
- Do not treat `dist/` as an independent source tree; fixes belong in active source packages and are verified again after rebuild.
- Materialized adapter registries under `dist/<adapter>/data/orchestrator-registry.json` are release-contract outputs, not source-edit targets.
- Historical runtime-era package implementations are preserved in git history and versioned release notes, not on the active maintainer path.

## Four-Layer Model

Forge changes should respect four layers:

1. `core`
2. `generated artifacts`
3. `workflow state`
4. `runtime tools`

The canonical layer contract lives in `docs/architecture/architecture-layers.md`.

In the current kernel-only line, `runtime tools` is a historical concept preserved through git history and versioned release notes, not as an active package role in the shipped product line.

## Active Package Roles

### `forge-core`

Canonical source-of-truth for:

- orchestrator registry
- host-neutral bootstrap wording
- deterministic scripts and remaining compatibility wrappers
- sibling skill activation contracts for skills sourced from `forge-skills`
- operator state and workflow-state semantics
- internal references and tests

`forge-core` should not depend on a single host-specific entry file.

### `forge-skills`

Canonical source-of-truth for public Forge sibling skills:

- one directory per shipped sibling skill
- each skill's `SKILL.md`
- skill-owned `references/**` companions colocated inside the owning skill directory
- skill-owned `commands/**` entrypoints colocated inside the owning skill directory

`forge-skills` is not an adapter bundle. Release builds materialize each directory as a public `dist/forge-*` skill bundle while keeping adapter bundles free of internal `skills/` subtrees.

### `forge-antigravity`

Adapter overlay for Antigravity:

- host-specific `SKILL.md`
- `agents/openai.yaml`
- natural-language session guidance for `resume`, `save context`, and `handover`
- one adapter data compatibility file: `data/preferences-compat.json`
- one adapter doc: `docs/antigravity-operator-surface.md`
- Antigravity-oriented host boundary wording
- sibling skill `forge-init` for workspace bootstrap and docs normalization

### `forge-codex`

Adapter overlay for Codex:

- Codex-specific `SKILL.md`
- `AGENTS.example.md` for workspace integration
- `AGENTS.global.md` for global Codex host takeover
- `delegate` routes directly to `forge-dispatching-parallel-agents`; session continuity is owned by `forge-session-management`.
- 3 adapter docs: `codex-operator-surface.md`, `smoke-test-checklist.md`, `smoke-tests.md`
- one adapter data override: `data/orchestrator-registry.json`
- one adapter tool: `tools/enable_windows_utf8.ps1`
- Codex-oriented host boundary wording
- sibling skill `forge-init` for workspace bootstrap and docs normalization

## Historical Runtime Tools

The runtime tools layer remains part of Forge history, but no longer lives on the active maintainer path.

Historical implementation evidence is preserved in git history and versioned release notes. It is not built, installed, or verified as part of the current kernel-only release line.

## Adapter Surface Differences

- Antigravity keeps the same session modes as core, but presents them as natural-language requests rather than dedicated wrapper aliases.
- Codex does not mirror those legacy wrappers; it keeps a thinner operator surface and adds native multi-agent dispatch instead.
- This is an intentional adapter-level UX difference, not a parity bug in `forge-core`.

## Release Flow

1. Start from `packages/forge-core`.
2. Copy core into `dist/forge-core`.
3. Refresh generated host artifacts from canonical sources before adapter overlays are copied.
4. Copy core into each adapter bundle under `dist/`.
5. Overlay adapter files on top of the copied core to materialize the adapter bundle and its registries.
6. Materialize each sibling skill directory from `packages/forge-skills/`.
7. Run verify on the built bundles.
8. Install from `dist/` into runtime paths with `scripts/install_bundle.py`.

This keeps one active implementation tree for the current product line.

## Rules

- Skill meaning changes belong in `packages/forge-skills/`.
- Host entry files and adapter UX wrappers belong in adapters.
- Historical runtime tools stay out of the current source tree unless a future roadmap explicitly restores them.
- Shared tests belong in `forge-core` or root `tests/`.
- Installed bundles under `dist/` are release artifacts, not development source.
- Materialized adapter registries in `dist/` are the contract to verify after build, not the place to edit overlay deltas.
- Canonical version lives in `/VERSION`, not in installed runtimes.
- `forge-core` must stay clean enough for future adapters such as `forge-claude`.
- If a feature is host-shaped, keep the engine in core only when it is truly reusable, and keep the wrapper in the adapter.
- If a feature changes release posture or post-release follow-up, keep the contract in core and let adapters mirror it through wording only.
