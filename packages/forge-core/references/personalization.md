# Forge Personalization

> Mục tiêu: giữ response-style preferences ở `forge-core` theo kiểu host-neutral để mỗi adapter chỉ cần thêm wrapper UX, không fork logic.

## Core Contract

- Schema canonical nằm tại `data/preferences-schema.json`
- Resolver canonical nằm tại `scripts/resolve_preferences.py`
- Persistence helper canonical nằm tại `scripts/write_preferences.py`
- Installed adapters mặc định dùng adapter-global state tại `<host-home>/<adapter-name>/state/preferences.json`
- `$FORGE_HOME/state/preferences.json` là explicit override cho test/dev; nếu không có installed adapter metadata hay override, core fallback về `~/.forge/state/preferences.json`
- Adapter có thể ship `data/preferences-compat.json` để map host-native preference payload sang canonical schema mà không fork core engine
- Workspace `.brain/preferences.json` có thể chứa thêm non-canonical preferences; core sẽ trả phần này qua field `extra` thay vì fork schema canonical
- Core cũng có thể suy ra `output_contract` từ `extra` cho các rule host-native như `language`, `orthography`, `tone_detail`, và `custom_rules`
- Adapter có thể thêm flow `customize`, nhưng không được đổi key names hay meaning của schema

## Supported Fields

| Field | Values | Default | Mục đích |
|------|--------|---------|---------|
| `technical_level` | `newbie`, `basic`, `technical` | `basic` | Điều chỉnh mức độ giải thích thuật ngữ |
| `detail_level` | `concise`, `balanced`, `detailed` | `balanced` | Điều chỉnh độ sâu và độ dài response |
| `autonomy_level` | `guided`, `balanced`, `autonomous` | `balanced` | Điều chỉnh mức độ chủ động khi đẩy task đi tiếp |
| `pace` | `steady`, `balanced`, `fast` | `balanced` | Điều chỉnh nhịp độ đẩy task đi tiếp |
| `feedback_style` | `gentle`, `balanced`, `direct` | `balanced` | Điều chỉnh độ gắt hay mềm khi chỉ ra gap/problem |
| `personality` | `default`, `mentor`, `strict-coach` | `default` | Điều chỉnh tone coaching |

## Resolution Order

1. Nếu có `--preferences-file`, dùng file đó và fail nếu file không tồn tại.
2. Nếu có adapter-global Forge state hợp lệ, đọc `state/preferences.json` của adapter đang chạy và preserve phần extra host-native ngoài schema canonical.
3. Nếu chưa có adapter-global file và có `--workspace`, đọc legacy `.brain/preferences.json` trong workspace đó cho canonical fallback; cùng file này cũng có thể chứa workspace-local extra preferences.
4. Nếu không có file hợp lệ, dùng defaults từ schema.

## Validation Rules

- Invalid JSON hoặc value sai enum sẽ fallback về default trong non-strict mode và trả warning.
- `--strict` biến warning thành hard failure.
- Alias như `strict_coach`, `beginner`, `verbose`, `low`, `high`, `slow`, `rapid`, `gentle`, `strict` được normalize về enum canonical.

## Response Style Resolver

Resolver không tạo host-specific command surface. Nó chỉ trả về response-style contract để adapter hoặc prompt entrypoint có thể áp dụng:

- terminology policy
- explanation policy
- verbosity/context depth
- decision/autonomy policy
- delivery pace
- feedback style
- tone/teaching/challenge style

Ngoài `response_style`, core có thể trả thêm `output_contract` khi workspace/global extras có rule host-native:

- language policy
- orthography / diacritics policy
- tone detail or honorific hints
- custom writing rules mà adapter nên giữ nguyên

## Persistence Flow

Khi adapter muốn ghi preferences:

```powershell
python scripts/write_preferences.py --technical-level newbie --pace fast --apply
```

Rule:

- Script merge với preferences hiện có theo mặc định
- `--replace` reset những field không được truyền về defaults của schema
- Adapter không được tự viết file theo schema riêng cho canonical state
- Workspace-local extra preferences, nếu có, sống ở `.brain/preferences.json` và không thay đổi meaning của 6 canonical fields

## Extra Preference Templates

Khi user chỉ hỏi về thiết lập ngôn ngữ hoặc cách viết, ưu tiên trỏ thẳng tới workspace `.brain/preferences.json` extras thay vì giải thích dài về 6 field canonical.

Mẫu 1: tiếng Việt có dấu

```json
{
  "language": "vi",
  "orthography": "vietnamese_diacritics",
  "custom_rules": [
    "Luôn giao tiếp với user bằng tiếng Việt có dấu.",
    "Không dùng tiếng Việt không dấu trong comment, summary, plan, review, hay text giải thích."
  ]
}
```

Mẫu 2: tiếng Anh

```json
{
  "language": "en",
  "custom_rules": [
    "Always communicate with the user in English."
  ]
}
```

Mẫu 3: giải thích bằng tiếng Việt, code/comment bằng tiếng Anh

```json
{
  "language": "vi",
  "custom_rules": [
    "Giải thích cho user bằng tiếng Việt có dấu.",
    "Giữ code identifiers, commit messages, và code comments bằng tiếng Anh khi phù hợp với repo."
  ]
}
```

Rule trả lời:

- Nếu user hỏi cách thiết lập ngôn ngữ, trả lời ngắn và trỏ đến `extra preferences` trong `.brain/preferences.json`
- Đưa 1 mẫu phù hợp nhất để user tự dán
- Chỉ nói về canonical preferences nếu user đang muốn đổi cả tone/detail/autonomy/pace/feedback

## Adapter Boundary

- `forge-antigravity`: có thể thêm `/customize` hoặc onboarding thin wrapper trên schema này, và có thể đọc workspace-local extra preferences cho host-native UX.
- `forge-codex`: nên giữ natural-language customize flow, không slash-heavy by default.
- `forge-claude` trong tương lai phải có thể tái sử dụng schema này gần như nguyên vẹn.
