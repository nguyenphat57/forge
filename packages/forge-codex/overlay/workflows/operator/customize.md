---
name: customize
type: flexible
triggers:
  - natural-language request to change tone, detail, autonomy, pace, or feedback style
  - natural-language request to lock language, diacritics, or writing conventions
  - optional alias: /customize
quality_gates:
  - Current preferences are inspected first
  - Durable changes use the core canonical schema and writer
  - Host-native language rules stay in workspace-local extras instead of forking the canonical schema
  - The response states what changed and how interaction will feel different
---

# Customize - Codex Preference Wrapper

> Mục tiêu: cho Codex một customize flow ngắn, đổi style phản hồi mà không thêm host-local schema.

## Process

Fast path cho language requests:

- Nếu user chỉ hỏi cách thiết lập ngôn ngữ, dấu tiếng Việt, hoặc writing conventions:
  - trỏ thẳng tới workspace `.brain/preferences.json` extras
  - đưa một mẫu ngắn có sẵn từ `packages/forge-core/references/personalization.md`
  - không cần giải thích dài về 6 field canonical

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

3. Nếu user muốn khóa language/orthography hoặc các writing rules host-native:
   - giữ chúng trong workspace `.brain/preferences.json`
   - không đẩy chúng vào 6 field canonical
   - ưu tiên trỏ user tới template phù hợp trong `packages/forge-core/references/personalization.md`

4. Preview hoặc persist bằng core writer:

```powershell
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct --apply
```

5. Trả lời ngắn:
   - field nào đã đổi
   - style mới sẽ khác như thế nào
   - nếu user hỏi về language rules, chỉ cần trỏ tới extra preferences + template phù hợp

## Activation Announcement

```text
Forge Codex: customize | update canonical preferences with minimal ceremony
```
