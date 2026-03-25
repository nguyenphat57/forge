---
name: customize
type: flexible
triggers:
  - natural-language request to change tone, detail, autonomy, pace, or feedback style
  - optional alias: /customize
quality_gates:
  - Current preferences are inspected first
  - Durable changes use the core canonical schema and writer
  - The response states what changed and how interaction will feel different
---

# Customize - Codex Preference Wrapper

> Mục tiêu: cho Codex một customize flow ngắn, đổi style phản hồi mà không thêm host-local schema.

## Process

1. Đọc preferences hiện tại:

```powershell
python scripts/resolve_preferences.py --format json
```

2. Map nhu cầu vào các field canonical:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. Preview hoặc persist bằng core writer:

```powershell
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct --apply
```

4. Trả lời ngắn:
   - field nào đã đổi
   - style mới sẽ khác như thế nào

## Activation Announcement

```text
Forge Codex: customize | update canonical preferences with minimal ceremony
```
