# Forge Current Operator Surface

## Source repo

The source repo now has one canonical operator entrypoint:

```powershell
python scripts/repo_operator.py <action> ...
```

Supported actions:

- `resume`
- `save`
- `handover`
- `help`
- `next`
- `run`
- `bump`
- `rollback`
- `customize`
- `init`
- `capture-continuity`

The dispatcher is the public source-repo surface.
Package-level scripts under `packages/forge-core/scripts/` are implementation detail unless the task is to edit or debug the engine itself.

## Installed runtime

Installed bundles keep their existing host-native workflow layout.
This refactor does not change installed Codex or Antigravity workflow paths.

## Machine-readable contract

`packages/forge-core/data/orchestrator-registry.json` now distinguishes:

- `repo_entrypoint`: the source-repo dispatcher contract
- `core_engine_entrypoint`: the underlying engine script or workflow contract used by bundles and generated docs

## Customize behavior

`customize` has one source-repo action and two underlying engine paths:

- preview path: `resolve_preferences.py`
- write path: `write_preferences.py`

If no mutation flags are supplied, the dispatcher resolves current preferences.
If write flags such as `--detail-level`, `--language`, or `--apply` are supplied, the dispatcher forwards to the writer.

## Current guidance rule

When documenting source-repo flows in this repository, always show `repo_operator.py`.
Do not reintroduce direct repo-root proxy file names into current docs.
