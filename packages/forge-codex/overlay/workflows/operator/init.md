---
name: init
type: flexible
triggers:
  - natural-language request to bootstrap a workspace for Forge
  - optional alias: /init
quality_gates:
  - Workspace is classified before suggesting a next step
  - No existing file is overwritten
  - Wrapper stays thin and avoids onboarding ceremony
---

# Init - Codex Workspace Bootstrap

> Mục tiêu: cho Codex một init flow tối thiểu để bắt đầu workspace mới mà không biến nó thành onboarding dài.

## Process

1. Preview skeleton:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --format json
```

2. Nếu cần tạo skeleton thật:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

`--seed-preferences` sẽ seed Codex-global preferences, không còn ghi vào workspace-local `.brain/preferences.json`.

3. Kết thúc bằng một next workflow duy nhất:
   - `brainstorm` cho workspace greenfield
   - `plan` cho workspace existing

## Activation Announcement

```text
Forge Codex: init | bootstrap workspace with one next step
```
