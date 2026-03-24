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

> Mục tiêu: cho Antigravity một `/init` rõ ràng để dùng Forge trên workspace mới mà không nhúng host ceremony vào core.

<HARD-GATE>
- Không overwrite file đã tồn tại.
- Không biến init thành onboarding dài dòng.
- Không đưa slash surface riêng của host vào core script.
</HARD-GATE>

## Process

1. Preview skeleton:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --format json
```

2. Nếu user muốn tạo skeleton thật:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

3. Nếu user muốn cá nhân hóa ngay, chuyển sang `/customize`.
4. Kết thúc bằng một next workflow duy nhất:
   - `brainstorm` cho workspace greenfield
   - `plan` cho workspace existing

## Output Contract

```text
Đã khởi tạo: [...]
Mode: [...]
Lam tiep: [...]
```

## Activation Announcement

```text
Forge Antigravity: init | bootstrap workspace, then choose one next workflow
```
