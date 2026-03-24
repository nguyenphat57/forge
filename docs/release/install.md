# Forge Install

## Mục tiêu

Cài bundle đã build từ `dist/` vào runtime thật, thay vì sửa trực tiếp thư mục đang chạy.
Install flow đồng bộ nội dung theo kiểu in-place sync để giảm rủi ro khi host đang giữ lock vào root folder runtime.

## Default targets

- `forge-antigravity` -> `~/.gemini/antigravity/skills/forge-antigravity`
- `forge-codex` -> `~/.codex/skills/forge-codex`

`forge-core` không có default target; nếu cần install bundle này, phải truyền `--target`.

## Quy trình chuẩn

```powershell
python scripts/verify_repo.py
python scripts/build_release.py
python scripts/install_bundle.py forge-antigravity --build
python scripts/install_bundle.py forge-codex --activate-codex
```

`--activate-codex` dành cho rollout Codex thật:

- sync `forge-codex` vào `~/.codex/skills/forge-codex`
- rewrite `~/.codex/AGENTS.md` để `forge-codex` là global orchestrator duy nhất
- retire `~/.codex/awf-codex`
- retire các skill global legacy theo pattern `~/.codex/skills/awf-*`

## Dry run

```powershell
python scripts/install_bundle.py forge-antigravity --dry-run
python scripts/install_bundle.py forge-codex --dry-run
python scripts/install_bundle.py forge-codex --dry-run --activate-codex
```

## Safety

- Script tự backup runtime cũ vào `.install-backups/` trước khi sync.
- Với `--activate-codex`, script backup thêm `~/.codex/AGENTS.md`, runtime legacy, và các skill legacy bị retire.
- Có thể đổi nơi backup bằng `--backup-dir`.
- Dùng `--no-backup` chỉ khi runtime đích là disposable.
- Không install vào `packages/`, `dist/`, hay root repo.
- Script prune file cũ không còn trong bundle mới, nhưng không cần xóa cả root folder runtime.

## Override target

```powershell
python scripts/install_bundle.py forge-core --target C:\path\to\custom\runtime
python scripts/install_bundle.py forge-antigravity --target C:\path\to\sandbox\forge-antigravity
```
