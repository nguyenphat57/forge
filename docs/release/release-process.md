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

## Core purity gate

Mọi thay đổi đụng `packages/forge-core` phải tự trả lời:

1. Feature này có còn đúng cho một adapter tương lai như `forge-claude` không?
2. Nó có phụ thuộc `GEMINI.md`, `AGENTS.md`, slash grammar, hay host metadata cụ thể không?
3. Phần nào là engine dùng chung, phần nào là wrapper riêng host?
4. Có đang kéo compatibility UX của một host vào core không?

Nếu change chỉ hợp với một host, giữ nó ở adapter.
Boundary policy chuẩn nằm ở `docs/architecture/adapter-boundary.md`.

## Versioning

- Canonical version nằm ở file `VERSION`.
- `build_release.py` ghi `version` và `git_revision` vào `BUILD-MANIFEST.json`.
- `install_bundle.py` ghi `INSTALL-MANIFEST.json` ở runtime đã cài.

## Promotion

- `forge-antigravity` hiện là adapter chín nhất cho rollout thật.
- `forge-codex` đã pass verify nội bộ, nhưng broad rollout vẫn cần soak trên host Codex thật.
- `forge-core` không được nhận host-specific UX chỉ để phục vụ một adapter hiện tại.
- Chỉ tag release sau khi `verify_repo.py` pass.
