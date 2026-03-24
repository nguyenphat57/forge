# Forge Bump Release

> Dùng khi cần chốt version mới và update release artifacts theo một checklist rõ ràng.

## Canonical Script

```powershell
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump patch
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump 2.0.0 --apply --release-ready
```

## Contract

- Đọc `VERSION`
- Tính `target_version` từ `patch|minor|major` hoặc explicit semver
- Preview hoặc apply đổi `VERSION` + `CHANGELOG.md`
- Trả về verification commands tiếp theo, không commit/push tự động

## Boundary

- Core chỉ lo version math và release checklist.
- Adapter có thể expose `/bump` hoặc natural-language wrapper, nhưng không được đổi explicit-only contract.
