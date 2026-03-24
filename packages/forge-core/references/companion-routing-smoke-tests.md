# Companion Routing Smoke Tests

> Dùng để stress test việc ghép `forge-antigravity` với companion skills. File này chỉ cần khi workspace chọn dùng companion/local layer; nó không phải smoke test bắt buộc của Forge core.

## Pass Criteria

- Forge vẫn là process/orchestration layer
- Companion skill được chọn đúng theo repo signals
- Runtime artifact rõ (ví dụ `pyproject.toml`, `go.mod`, `*.csproj`) có thể đủ để kéo companion phù hợp khi router inventory đã rõ
- Router doc được dùng như reference, không bị coi là skill
- Router filename không bắt buộc phải chứa `skill-map` nếu `AGENTS.md` trỏ thẳng đúng file
- Không load thừa nhiều companion skills khi một skill là đủ
- Verification/evidence gate vẫn theo Forge

Có thể chạy `python scripts/run_smoke_matrix.py --suite router-check` để bắt drift entrypoint-level trước khi làm manual companion smoke trên host thật.

## Scenario 1 - Pure Web Repo

```text
Prompt:
Fix bug ở React page khi route `/orders` render sai sau khi refactor.
```

Expected:
- Forge detect BUILD/DEBUG
- Companion skill: web/runtime skill duy nhất
- Không load mobile/native/database skill nếu repo signal không cần

## Scenario 2 - Android Native Bridge

```text
Prompt:
Fix custom Capacitor plugin không nhận callback sau khi app resume.
```

Expected:
- Forge + mobile shell companion + native bridge companion
- Không chỉ dừng ở web React skill
- Verification nhắc tới sync/build/device smoke

## Scenario 3 - Schema / RLS Change

```text
Prompt:
Thêm policy chỉ cho admin đọc bảng notifications.
```

Expected:
- Forge + database/security companion
- Không kéo UI/web skill nếu task chỉ nằm ở data boundary

## Scenario 4 - Workspace-Local Companion

```text
Prompt:
Fix outbox bị kẹt ở processing sau khi app online lại.
```

Expected:
- Forge đọc `AGENTS.md` hoặc workspace map nếu có
- Chọn local offline-sync companion nếu workspace đã định nghĩa
- Không đoán theo generic TS/web skill một cách duy nhất

## Scenario 4B - Runtime Signal Only

```text
Prompt:
Implement endpoint.
```

Expected:
- Nếu workspace inventory có `python-fastapi` và repo signal có `pyproject.toml`, Forge vẫn có thể chọn companion đó
- Không buộc prompt phải ghi từ `python` một cách tự nhiên

## Scenario 5 - Router Doc Is Not Skill

```text
Prompt:
Use the workspace map to choose the right skill for this deploy task.
```

Expected:
- Agent có thể đọc router doc
- Nhưng vẫn load skill thật từ `SKILL.md`
- Không xem router doc là companion skill

## Scenario 6 - Minimal-Set Rule

```text
Prompt:
Deploy web SPA lên Cloudflare sau khi đổi một route fallback.
```

Expected:
- Forge + web companion + deploy companion
- Không load mobile/native/database companions nếu không cần

## Scenario 7 - Router Filename Flexibility

```text
Setup:
AGENTS.md trỏ tới `.agent/router.md`
```

Expected:
- Workspace router checker resolve đúng `.agent/router.md`
- Không fail chỉ vì file không chứa chuỗi `skill-map`

## Failure Signs

- Load quá 4-5 skills cho task vừa/nhỏ mà không có lý do
- Router doc bị coi như skill executable
- Companion skill override verification/evidence gate
- Chọn companion chỉ vì agent quen stack đó, không dựa vào repo signals
