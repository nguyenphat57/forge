# Forge Release Process

## Source of truth

- Chỉ sửa trong `packages/forge-core` và các adapter overlays.
- `dist/` là release artifact.
- Runtime đã cài đặt không phải nơi để dev trực tiếp.

## Release gate

1. Cập nhật source trong monorepo.
2. Chạy `python scripts/verify_repo.py`.
3. Build artifact bằng `python scripts/build_release.py`.
4. Install hoặc publish từ `dist/`.
5. Chạy smoke/canary theo host trước khi promote rộng.

## Versioning

- Canonical version nằm ở file `VERSION`.
- `build_release.py` ghi `version` và `git_revision` vào `BUILD-MANIFEST.json`.
- `install_bundle.py` ghi `INSTALL-MANIFEST.json` ở runtime đã cài.

## Promotion

- `forge-antigravity` hiện là adapter chín nhất cho rollout thật.
- `forge-codex` đã pass verify nội bộ, nhưng broad rollout vẫn cần soak trên host Codex thật.
- Chỉ tag release sau khi `verify_repo.py` pass.
