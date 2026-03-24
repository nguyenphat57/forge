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

> Muc tieu: cho Codex mot init flow toi thieu de bat dau workspace moi ma khong bien no thanh onboarding dai.

## Process

1. Preview skeleton:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --format json
```

2. Neu can tao skeleton that:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

3. Ket thuc bang mot next workflow duy nhat:
   - `brainstorm` cho workspace greenfield
   - `plan` cho workspace existing

## Activation Announcement

```text
Forge Codex: init | bootstrap workspace with one next step
```
