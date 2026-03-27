---
name: customize
type: flexible
triggers:
  - shortcut: /customize
  - user wants to change explanation depth, tone, autonomy, pace, or feedback style
  - user asks how to set language, diacritics, or writing conventions
quality_gates:
  - Current preferences are inspected before changing anything
  - Durable changes use the core canonical schema and writer
  - Durable language rules live in adapter-global extras; workspace `.brain/preferences.json` is only for workspace-specific overrides
  - Output states what changed and what response style will feel different
---

# Customize - Antigravity Preference Wrapper

> Mục tiêu: cho user Antigravity một bề mặt `/customize` rõ ràng, nhưng mọi thay đổi bền vững vẫn đi qua contract canonical của Forge.

<HARD-GATE>
- Không tạo key riêng cho Antigravity trong adapter-global state.
- Không overwrite toàn bộ preferences nếu user chỉ đổi một vài field.
- Không đổi routing hay gate logic; workflow này chỉ đổi response style.
- Đọc bằng `resolve_preferences.py` là read-only, không được mutate state để “xem thử”.
- Legacy single-file state của Antigravity có thể được migrate ở write/apply path; sau migration canonical và extras sẽ tách file.
- Workspace `.brain/preferences.json` chỉ dùng cho legacy fallback hoặc override theo repo, không phải nơi mặc định để lưu language rules bền vững.
</HARD-GATE>

## Process

Fast path cho language requests:

- Nếu user chỉ hỏi cách đặt ngôn ngữ, dấu tiếng Việt, hay quy ước viết:
  - ưu tiên chỉ thẳng tới durable adapter-global update qua `scripts/write_preferences.py`
  - chỉ trỏ sang workspace `.brain/preferences.json` khi họ muốn rule chỉ áp dụng cho repo hiện tại
  - dùng lại template ngắn trong `references/personalization.md`

1. Đọc preferences hiện tại:

```powershell
python scripts/resolve_preferences.py --format json
```

2. Map user intent vào các field canonical khi yêu cầu liên quan tới style:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. Nếu user muốn khóa `language`, `orthography`, hoặc host-native writing rules:
   - persist chúng qua adapter-global extras bằng `scripts/write_preferences.py`
   - không nhét chúng vào 6 canonical fields
   - chỉ dùng `.brain/preferences.json` cho override theo workspace

4. Preview hoặc persist bằng core writer:

```powershell
python scripts/write_preferences.py --detail-level detailed --pace fast --feedback-style direct
python scripts/write_preferences.py --detail-level detailed --pace fast --feedback-style direct --apply
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
```

5. Trả lời ngắn:
   - preference nào đã đổi
   - style phản hồi sẽ khác thế nào
   - nếu có workspace-only override thì nói rõ nó vẫn tách khỏi adapter-global state
   - nếu có migration legacy state thì nêu rõ canonical và extras đã tách file

## Output Contract

```text
Đã đổi:
- [...]

Style mới:
- [...]

Override theo workspace:
- [...]

Tác động:
- [...]
```

## Activation Announcement

```text
Forge Antigravity: customize | update canonical preferences, keep workspace overrides explicit
```
