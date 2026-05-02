# Forge Current Operator Surface

## Source Repo

The source repo no longer has a repo-root operator entrypoint.

Notes:

- Workspace bootstrap and docs normalization now route through the sibling skill `forge-init`, not a repo operator action.
- Release bump preparation now routes through the sibling skill `forge-bump-release`, not a repo operator action.
- Live deploy and production-readiness work now route through the sibling skill `forge-deploy`, not a repo operator action.
- `forge-session-management` resume reads real artifacts and may auto-seed canonical `workflow-state` from a legacy JSON artifact or the latest plan/spec when no canonical root exists yet.
- Guidance, next-step selection, and command execution stay natural-language first through Forge skills and host-native tools.
- Continuity capture remains internal runtime tooling and is not part of the public repo operator surface.
- Package-level runtime code lives in owner `commands/` directories, with reusable helpers under `packages/forge-core/shared/`. Treat both as implementation detail unless the task is to change runtime internals.

## Context Persistence Boundary

- Resume may auto-seed `.forge-artifacts/workflow-state/<project>/latest.json` from a legacy workflow artifact or the latest plan/spec when no canonical workflow-state root exists.
- Workflow-state is the automatic execution-state layer for stages, packets, gates, reviews, runs, and related Forge transitions; it is not written by `save context`.
- `save context` writes `.brain/session.json` as an explicit session snapshot and writes `.brain/handover.md` only when handover is requested.
- Selective closeout writes lazily at completion only when durable signals exist; it may write `.brain/session.json`, `.brain/handover.md`, `.brain/decisions.json`, or `.brain/learnings.json`.
- `learning` entries are durable only through selective closeout into `.brain/learnings.json`; normal `save context` does not create learning records.
- `forge-init` creates or normalizes bootstrap docs only; it does not create `.brain/session.json` by default.
- Raw `error` output is not stored as a durable `.brain` record. Persist recurring failures as a blocker, risk, verification note, decision, or learning with evidence.

## Installed Runtime

Installed Codex and Antigravity adapters expose `forge-codex` or `forge-antigravity` as the bootstrap skill and install the sibling Forge skill family next to it.

Workflow selection happens through bootstrap markdown and host-native skill discovery. Compatibility workflow files remain internal support wrappers rather than the public action surface.

## Machine-Readable Contract

`packages/forge-core/data/orchestrator-registry.json` distinguishes:

- `skill_catalog`: static sibling skill metadata and compatibility workflow paths
- `repo_operator_surface`: the source-repo operator contract
- `host_operator_surface`: the installed-host public surface contract

These sections are catalogs and metadata, not a deterministic routing engine.

## Current Guidance Rule

When documenting source-repo flows in this repository, show Forge sibling skills for process activation, release bump preparation, and deploy work.

Do not reintroduce repo-root operator scripts or describe workflow files as the primary activation surface.

