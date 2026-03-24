# Forge Install

## Mục tiêu

Cài bundle đã build từ `dist/` vào runtime thật, thay vì sửa trực tiếp thư mục đang chạy.
Install flow dong bo noi dung theo kieu in-place sync de giam rui ro khi host dang giu lock vao root folder runtime.

## Default targets

- `forge-antigravity` -> `~/.gemini/antigravity/skills/forge-antigravity`
- `forge-codex` -> `~/.codex/skills/forge-codex`

`forge-core` không có default target; nếu cần install bundle này, phải truyền `--target`.

## Quy trình chuẩn

```powershell
python scripts/verify_repo.py
python scripts/build_release.py
python scripts/install_bundle.py forge-antigravity --build
python scripts/install_bundle.py forge-codex
```

## Dry run

```powershell
python scripts/install_bundle.py forge-antigravity --dry-run
python scripts/install_bundle.py forge-codex --dry-run
```

## Safety

- Script tự backup runtime cũ vào `.install-backups/` trước khi sync.
- Có thể đổi nơi backup bằng `--backup-dir`.
- Dùng `--no-backup` chỉ khi runtime đích là disposable.
- Không install vào `packages/`, `dist/`, hay root repo.
- Script prune file cu khong con trong bundle moi, nhung khong can xoa ca root folder runtime.

## Override target

```powershell
python scripts/install_bundle.py forge-core --target C:\path\to\custom\runtime
python scripts/install_bundle.py forge-antigravity --target C:\path\to\sandbox\forge-antigravity
```
