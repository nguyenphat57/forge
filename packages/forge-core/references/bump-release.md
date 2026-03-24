# Forge Bump Release

> Dung khi can chot version moi va update release artifacts theo mot checklist ro rang.

## Canonical Script

```powershell
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump patch
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump 2.0.0 --apply --release-ready
```

## Contract

- Doc `VERSION`
- Tinh `target_version` tu `patch|minor|major` hoac explicit semver
- Preview hoac apply doi `VERSION` + `CHANGELOG.md`
- Tra ve verification commands tiep theo, khong commit/push tu dong

## Boundary

- Core chi lo version math va release checklist.
- Adapter co the expose `/bump` hoac natural-language wrapper, nhung khong duoc doi explicit-only contract.
