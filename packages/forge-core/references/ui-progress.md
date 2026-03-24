# UI Progress Tracking

> Dùng cho task frontend/visualize kéo dài, nhiều màn hình, hoặc có handoff qua nhiều bước.

## Why

Forge route tốt nhưng task UI dài thường dễ trôi:
- đã chốt brief chưa?
- đang ở interaction model hay implementation?
- còn review responsive/a11y chưa?

Artifact progress giúp tránh mơ hồ mà không cần cả dashboard lớn.

## Command

### Frontend

```powershell
python scripts/track_ui_progress.py "Checkout tablet refresh" --mode frontend --stage implementation --status active
```

### Visualize

```powershell
python scripts/track_ui_progress.py "Kitchen dashboard exploration" --mode visualize --stage interaction-model --status active
```

Artifact mặc định:

```text
.forge-artifacts/ui-progress/<mode>/<task>.md
.forge-artifacts/ui-progress/<mode>/<task>.json
```

## Recommended Stages

### frontend

- `brief`
- `system-check`
- `implementation`
- `responsive-a11y-review`
- `handover`

### visualize

- `brief`
- `interaction-model`
- `spec-or-mockup`
- `states-platform-review`
- `handover`

## Use Rule

- Không bắt buộc cho task nhỏ.
- Nên dùng khi task UI kéo dài qua nhiều message, nhiều màn hình, hoặc dễ handoff giữa design và implementation.
