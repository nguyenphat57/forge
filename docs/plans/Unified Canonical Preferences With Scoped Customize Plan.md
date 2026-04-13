# Plan: Unified Canonical Preferences With Scoped Customize

Status: implemented

## Summary
Replace the current split-file model (`preferences.json` + `extra_preferences.json`) with a single canonical `preferences.json` per scope, and make workspace persistence first-class. `customize` becomes a scoped preference flow that lists effective preferences, lets the operator lock only the chosen keys, and applies them to `global`, `workspace`, or `both`.

The new canonical field set is the current six style fields plus the currently persisted “extra” fields: `language`, `orthography`, `tone_detail`, `output_quality`, `custom_rules`, and `delegation_preference`. `extra_preferences.json` is retired from steady-state storage and survives only as legacy migration input.

## Key Changes
### Canonical model and resolution
- Expand the canonical schema so `preferences.json` is a single flat object containing all canonical fields.
- Keep one global file at `state/preferences.json` and one workspace file at `.brain/preferences.json`.
- Resolve effective preferences per key with strict precedence: `workspace > global > defaults`.
- Remove `extra` from the public resolver/writer payload; keep `output_contract` and `response_style` as derived outputs from the flat canonical object.
- Add a per-key source map to the customize preview/resolver output so the UI/workflow can show which values come from defaults, global, or workspace.

### Customize flow and write semantics
- Keep `python scripts/repo_operator.py customize ...` as the public entrypoint.
- Split customize behavior into:
  - preview/catalog path: returns effective preferences, grouped display sections, per-key sources, warnings, and allowed scopes
  - apply path: writes only explicitly selected keys
- Add `--scope global|workspace|both` to the write path; default to `global` to preserve today’s behavior unless the user chooses otherwise.
- Define `both` as: write the same selected keys to both files; workspace continues to override global in that repo.
- Treat “locked selections” as workflow state only: the engine never infers neighboring keys; it writes only the keys explicitly chosen by the user or passed by flags.
- Allow display grouping in `customize`, but make it presentation-only; storage and resolver semantics stay flat canonical.

### Migration and compatibility
- Unified `preferences.json` becomes the only steady-state file format for both scopes.
- Legacy read path:
  - if unified file exists, use it
  - otherwise, read legacy global split files or legacy workspace `.brain/preferences.json`
- First `--apply` auto-migrates legacy state into the new unified target file, then writes backups such as `preferences.json.legacy.bak` and `extra_preferences.json.legacy.bak`.
- After successful migration, legacy `extra_preferences.json` is removed from active state and no longer referenced in generated host artifacts, install manifests, docs, or tests.
- Keep migration compatibility in code only as long as needed to read old installs/workspaces that have not yet been rewritten.

### Surface and artifact updates
- Update the core schema, resolver, writer, and any compat helpers so there is no runtime concept of `extra_path`, `changed_extra_fields`, or split-file bootstrap.
- Update generated AGENTS/GEMINI templates, install reports/manifests, bundle metadata, and operator docs to reference only one preferences file per scope.
- Update `customize` docs/wrappers so workspace is no longer described as merely “legacy fallback”; it is a supported explicit scope.
- Keep `output_contract` generation working from canonical fields so host locale behavior remains intact after the storage cut.

## Public Interface Changes
- `write_preferences.py`
  - add `--scope global|workspace|both`
  - output a single `changed_fields` list over the unified canonical key set
  - return one or two target paths depending on scope, not `path` + `extra_path`
- `resolve_preferences.py`
  - return one flat `preferences` object
  - remove `extra` from the public JSON contract
  - include per-key effective source metadata for customize/useful debugging
- `repo_operator.py customize`
  - preview path should surface the unified catalog and scope options
  - write path should forward `--scope` and only explicit updates

## Test Plan
- Resolver tests:
  - load unified global preferences
  - load unified workspace preferences
  - verify per-key precedence `workspace > global > defaults`
  - verify `output_contract` and `response_style` still derive correctly from flat canonical input
- Migration tests:
  - read legacy split global state
  - auto-migrate split state on first apply
  - back up old files and stop using `extra_preferences.json` afterward
  - preserve legacy workspace `.brain/preferences.json` migration behavior
- Writer tests:
  - write `global`
  - write `workspace`
  - write `both`
  - confirm only selected keys change and workspace shadows global when both are present
- Host/install tests:
  - generated AGENTS/GEMINI/install manifests reference only unified preference paths
  - installed bundles resolve and write preferences without any `extra_preferences.json`
- End-to-end verification:
  - targeted preference/customize test suites pass
  - full `python scripts/verify_repo.py` passes after docs/generated artifact refresh

## Assumptions and Defaults
- Workspace-local preferences remain at `.brain/preferences.json`.
- The unified canonical field set is: `technical_level`, `detail_level`, `autonomy_level`, `pace`, `feedback_style`, `personality`, `language`, `orthography`, `tone_detail`, `output_quality`, `custom_rules`, `delegation_preference`.
- `customize` display grouping may remain split for readability, but those groups are not storage or schema boundaries.
- Default write scope is `global`.
- `both` means write both now; workspace wins at resolution time in that repo.
- The cut is intentionally breaking at the public JSON payload level: `extra` is removed rather than preserved as a long-term compatibility shim.
