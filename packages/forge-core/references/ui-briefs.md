# UI Briefs

> Dùng khi task là `frontend` hoặc `visualize` ở mức vừa/lớn, hoặc khi visual direction còn mơ hồ.

## Why This Exists

`frontend` và `visualize` đều cần một first artifact rõ ràng trước khi lao vào component hoặc mockup:

- `frontend`: frontend brief
- `visualize`: visual brief

Brief này không thay design system của project. Nó chỉ chốt:
- scope
- visual direction
- interaction model
- states
- responsive/a11y boundaries
- stack/platform lens

## Generate A Brief

### Frontend brief

```powershell
python scripts/generate_ui_brief.py "Refresh checkout layout for tablet POS" `
  --mode frontend `
  --stack react-vite `
  --platform tablet `
  --screen checkout
```

### Visual brief

```powershell
python scripts/generate_ui_brief.py "Explore a calmer dashboard direction for kitchen mode" `
  --mode visualize `
  --stack mobile-webview `
  --platform tablet `
  --screen kitchen-dashboard
```

## Persisted Master + Page Override Pattern

Khi task kéo dài nhiều bước hoặc nhiều màn hình, thêm `--persist`:

```powershell
python scripts/generate_ui_brief.py "..." --mode frontend --persist --project-name "LamDiFood POS" --screen checkout
```

Artifact tạo ra:

```text
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.md
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.json
.forge-artifacts/ui-briefs/<project-slug>/<mode>/pages/<screen>.md
```

Reading order:
1. `MASTER.md`
2. `pages/<screen>.md` nếu screen có override

## When To Reuse vs Regenerate

Reuse brief hiện có khi:
- visual direction không đổi
- cùng screen family
- cùng stack/platform constraints

Regenerate hoặc update brief khi:
- thêm screen mới
- đổi visual direction
- đổi platform lens
- task chuyển từ concept sang implementation hoặc ngược lại

## Minimum Brief Quality

- Có scope rõ
- Có states rõ: default/loading/empty/error
- Có responsive hoặc platform note
- Có accessibility boundary
- Có stack-specific focus hoặc watchouts

## Validate A Persisted Brief

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
```

Hoặc:

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/visualize --mode visualize --screen dashboard
```
