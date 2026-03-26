# Forge Bump Release

> Use when you need to finalize a new version and update release artifacts according to a clear checklist.

## Canonical Script

```powershell
python scripts/prepare_bump.py --workspace C:\path\to\workspace
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump patch
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump 2.0.0 --apply --release-ready
```

## Contract

- Read `VERSION`
- If user requests bump but doesn't state level, infer `patch|minor|major` from git diff since last changed `VERSION`
- Calculate `target_version` from inference level, `patch|minor|major`, or explicit semver
- Preview or apply to change `VERSION` + `CHANGELOG.md`
- Returns the next verification commands, not commit/push automatically
- If the inference has low confidence, a warning must be issued and override allowed with `--bump`

## Boundary

- Core only takes care of version math and release checklist.
- The adapter can expose `/bump` or a natural-language wrapper, but cannot commit/push itself or assume release-ready.
