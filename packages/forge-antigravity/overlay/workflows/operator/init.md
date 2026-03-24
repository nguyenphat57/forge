---
name: init
type: flexible
triggers:
  - shortcut: /init
  - first-run workspace bootstrap
quality_gates:
  - Workspace is classified as greenfield or existing before suggesting next steps
  - No existing file is overwritten
  - Ends with one recommended next workflow
---

# Init - Antigravity Workspace Bootstrap

> Muc tieu: cho Antigravity mot `/init` ro rang de dung Forge tren workspace moi ma khong nhung host ceremony vao core.

<HARD-GATE>
- Khong overwrite file da ton tai.
- Khong bien init thanh onboarding dai dong.
- Khong dua slash surface rieng cua host vao core script.
</HARD-GATE>

## Process

1. Preview skeleton:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --format json
```

2. Neu user muon tao skeleton that:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

3. Neu user muon ca nhan hoa ngay, chuyen sang `/customize`.
4. Ket thuc bang mot next workflow duy nhat:
   - `brainstorm` cho workspace greenfield
   - `plan` cho workspace existing

## Output Contract

```text
Da khoi tao: [...]
Mode: [...]
Lam tiep: [...]
```

## Activation Announcement

```text
Forge Antigravity: init | bootstrap workspace, then choose one next workflow
```
