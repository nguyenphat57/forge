---
name: customize
type: flexible
triggers:
  - shortcut: /customize
  - user wants to change explanation depth, tone, autonomy, pace, or feedback style
quality_gates:
  - Current preferences are inspected before changing anything
  - Durable changes use the core canonical schema and writer
  - Output states what changed and what response style will feel different
---

# Customize - Antigravity Preference Wrapper

> Mục tiêu: cho user Antigravity một bề mặt `/customize` rõ ràng, nhưng vẫn ghi vào schema canonical của Forge.

<HARD-GATE>
- Không tạo key riêng cho Antigravity.
- Không overwrite toàn bộ preferences nếu user chỉ đổi một vài field.
- Không đổi routing/gate logic; workflow này chỉ đổi response style.
</HARD-GATE>

## Process

1. Đọc preferences hiện tại:

```powershell
python scripts/resolve_preferences.py --workspace <workspace> --format json
```

2. Map user intent vào các field canonical:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. Preview hoặc persist bằng core writer:

```powershell
python scripts/write_preferences.py --workspace <workspace> --detail-level detailed --pace fast --feedback-style direct
python scripts/write_preferences.py --workspace <workspace> --detail-level detailed --pace fast --feedback-style direct --apply
```

4. Trả lời ngắn:
   - preferences mới
   - field nào đã đổi
   - response sẽ khác như thế nào

## Output Contract

```text
Đã đổi:
- [...]

Style mới:
- [...]

Tác động:
- [...]
```

## Activation Announcement

```text
Forge Antigravity: customize | update canonical preferences, not host-local hacks
```
