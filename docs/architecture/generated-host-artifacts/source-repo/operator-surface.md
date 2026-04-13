# Forge Current Operator Surface

## Source Repo

The source repo now has one canonical operator entrypoint:

```powershell
python scripts/repo_operator.py <action> ...
```

Supported public actions:

{{FORGE_REPO_PUBLIC_ACTIONS}}

Notes:

- `help`, `next`, and `resume` may auto-seed canonical `workflow-state` from a legacy JSON artifact or the latest plan/spec when no canonical root exists yet.
- Continuity capture remains internal engine tooling and is not part of the public repo operator surface.

The dispatcher is the public source-repo surface.
Package-level scripts under `packages/forge-core/scripts/` are implementation detail unless the task is to edit or debug the engine itself.
This current surface assumes the kernel-only product line and only routes the shipped kernel and host-adapter entrypoints.

## Installed Runtime

Installed bundles keep their existing host-native workflow layout.
This refactor does not change installed Codex or Antigravity workflow paths.

## Machine-Readable Contract

`packages/forge-core/data/orchestrator-registry.json` now distinguishes:

- `repo_operator_surface`: the source-repo dispatcher contract
- `host_operator_surface`: the installed-host public surface contract

Both surfaces keep the same metadata schema; fields that do not apply stay empty instead of introducing separate schemas.

## Current Guidance Rule

When documenting source-repo flows in this repository, always show `repo_operator.py`.
Do not reintroduce direct core-script guidance outside `repo_operator.py`.
