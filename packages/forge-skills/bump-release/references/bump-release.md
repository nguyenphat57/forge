# Forge Bump Release Reference

Use this reference when applying `forge-bump-release` and the command flags or output fields matter.

## Canonical Script

```powershell
python references/scripts/prepare_bump.py --workspace <workspace>
python references/scripts/prepare_bump.py --workspace <workspace> --bump patch
python references/scripts/prepare_bump.py --workspace <workspace> --bump 2.0.0 --apply --release-ready
```

## Contract

- Read `VERSION`.
- If user requests a bump but does not state the level, infer `patch|minor|major` from git diff since the last changed `VERSION`.
- Calculate `target_version` from inference level, `patch|minor|major`, or explicit semver.
- Preview or apply changes to `VERSION` and `CHANGELOG.md`.
- Return next verification commands; do not commit, push, tag, publish, or claim release-ready.
- If inference confidence is low, warn and allow override with `--bump patch|minor|major`.

## JSON Fields

The script preserves these fields:

```text
status, workspace, current_version, target_version, bump, selected_bump,
bump_source, inference_confidence, inferred_from, inference_reasons,
analysis_changed_files, applied, changed_files, verification_commands, warnings
```

## Response Shape

Report:

- version from -> to
- bump source: explicit or inferred
- confidence and warnings, when present
- files changed or planned
- verification commands to run next

Do not use release-ready wording unless the listed verification was actually run and reported.
