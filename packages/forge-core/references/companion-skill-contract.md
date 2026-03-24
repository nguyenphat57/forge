## Companion Skill Contract

> Mục tiêu: mô tả cách Forge ghép thêm runtime/framework skill mà không làm mờ orchestration, verification, và reporting của Forge.
> Đây là lớp mở rộng tùy chọn. Forge core phải tự hoạt động tốt ngay cả khi không có companion hay local skill nào.

## Khi nào đọc file này

- Khi tạo companion skill cho Python, Java, Go, .NET, hoặc framework-specific stack
- Khi update Forge để ghép companion skill mới
- Khi runtime của repo đã rõ và bạn cần chốt boundary giữa Forge với runtime/framework layer

Không cần đọc file này nếu:
- repo chưa có companion/local skill nào
- repo mới và Forge core đã đủ để plan/build/debug/review
- task hiện tại không cần runtime/framework layer riêng

## Default Operating Mode

Mặc định Forge chạy theo:

```text
Forge core workflows + Forge domains
```

Không phải:

```text
Forge + companion skill bắt buộc
```

Companion skill chỉ xuất hiện khi nó tăng độ chính xác rõ ràng.

## Mental Model

Forge là **process/orchestration layer**.  
Companion skill là **runtime/framework layer**.

Forge quyết định:
- intent routing
- complexity
- verification gate
- evidence threshold
- residual-risk reporting
- handover/report shape

Companion skill quyết định:
- idiom code theo ngôn ngữ
- framework conventions
- file/folder conventions của stack
- build/test/run command discovery theo runtime
- dependency/toolchain detail

## Trigger Contract

Chỉ load companion skill khi có **repo signal rõ ràng** hoặc user chỉ rõ stack.

| Runtime | Repo signal thường gặp |
|---------|------------------------|
| Node/TS | `package.json` |
| Python | `pyproject.toml`, `requirements.txt` |
| Go | `go.mod` |
| Java/Kotlin | `pom.xml`, `build.gradle` |
| .NET | `*.csproj`, `*.sln` |

Không đoán runtime chỉ từ tên folder, tên biến, hay thói quen của agent.

## Integration Order

```text
1. Forge detect intent + complexity
2. Forge chọn process/domain skills chính đủ để làm việc
3. Forge detect runtime từ source-of-truth artifact
4. Nếu runtime rõ và companion skill thực sự giúp tăng độ chính xác -> load companion skill
5. Companion cung cấp stack-specific conventions và commands
6. Forge áp verification gate, reporting, và handover
```

Nếu không có companion skill phù hợp, dừng ở bước 3 và tiếp tục bằng Forge core.

## Ownership Boundary

| Khu vực | Chủ sở hữu |
|---------|------------|
| Intent routing | Forge |
| Complexity assessment | Forge |
| Scope control | Forge |
| Verification-first / test-first gate | Forge |
| Evidence before claims | Forge |
| Output/handover template | Forge |
| Coding idiom theo ngôn ngữ | Companion |
| Framework structure | Companion |
| Stack-specific command discovery | Companion |
| Dependency/toolchain detail | Companion |

## Conflict Resolution

Nếu Forge và companion skill khác nhau:

- Theo Forge cho:
  - verification
  - evidence threshold
  - reporting
  - residual risk
  - scope discipline
- Theo companion skill cho:
  - code style theo runtime
  - framework structure
  - stack-specific test/build/run commands
  - migration/tooling conventions đặc thù

Companion skill không được:
- bỏ qua failing test/reproduction gate của Forge khi harness khả thi
- nới lỏng evidence chỉ vì framework quen thuộc
- thay handover/report của Forge bằng format riêng
- biến chính nó thành một orchestrator thứ hai

## Optional Workspace-Local Layer

Companion skill có thể ở:
- global skill library
- workspace-local skill folder gần repo

Workspace-local layer chỉ áp dụng khi workspace thật sự chọn mô hình `global orchestrator + local companions`.

Workspace-local companion skill là hợp lệ khi:
- workspace có `AGENTS.md` hoặc router doc trỏ tới nó
- skill thật có `SKILL.md`
- repo signals khớp với layer mà skill đó phụ trách

Ưu tiên workspace-local companion skill khi:
- nó bám domain/runtime riêng của repo
- router doc của workspace đã chỉ rõ
- không có conflict với evidence gate của Forge

Nếu workspace không có local layer, không cần tạo giả router hay local inventory để dùng Forge.

## Router Docs vs Skill Docs

- `SKILL.md` là triggerable skill entrypoint
- `AGENTS.md` hoặc workspace skill map là router/reference doc
- Router doc có thể nói **nên dùng skill nào**, nhưng bản thân router doc không thay thế `SKILL.md`
- Không dùng router doc như một skill giả để nhét logic runtime thay cho skill thật

## Workspace Router Contract

Phần này chỉ áp dụng cho workspace chọn mô hình `global orchestrator + local companion skills`.

Nên giữ:
- `AGENTS.md` mỏng:
  - nhận diện workspace
  - read order
  - link sang router/source-of-truth doc
- workspace skill map làm source-of-truth cho:
  - inventory local skills
  - routing precedence
  - fallback rules
  - examples và smoke-test links

Không nên:
- lặp cùng một bảng routing ở cả `AGENTS.md` và workspace map
- nhét inventory đầy đủ local skills vào nhiều nơi
- để từng local skill tự mô tả lại toàn bộ kiến trúc workspace
- sửa router docs xong nhưng không chạy checker để bắt drift

## Recommended Workspace Layout

```text
workspace/
├── AGENTS.md
└── .agent/
    ├── workspace-skill-map.md
    ├── routing-smoke-tests.md
    ├── local-skill-maintenance.md
    └── skills/
        ├── skill-a/SKILL.md
        └── skill-b/SKILL.md
```

Tên file có thể khác, nhưng vai trò nên giữ nguyên.

## Minimum Companion Output

Khi được load, companion skill nên nhanh chóng xác nhận:

```text
Runtime context:
- Stack/framework: [...]
- Repo signals: [...]
- Primary commands: [build/test/run/lint]
- Conventions cần giữ: [...]
- Risks/constraints đặc thù stack: [...]
```

Không cần lặp lại toàn bộ guardrail của Forge.

## Recommended Activation Pattern

```text
Forge: [intent] | [complexity] | Skills: [forge skills] + [companion skill]
```

Ví dụ:

```text
Forge: BUILD | medium | Skills: plan + build + backend + python-fastapi
Forge: DEBUG | small | Skills: debug + test + dotnet-webapi
```

## Design Rule For Companion Skills

Companion skill nên:
- giả định Forge đã giữ process discipline
- đi thẳng vào runtime-specific heuristics
- ưu tiên command discovery từ repo thật
- không hardcode framework nếu artifact chưa chứng minh
- giữ reference ngắn, tránh biến companion thành orchestrator thứ hai

## Anti-Patterns

- Companion skill tự route intent thay Forge
- Companion skill tự quyết định skip verification vì "stack này khó test"
- Forge nhúng quá nhiều idiom của một ngôn ngữ vào `build.md` hoặc `backend.md`
- Load cùng lúc nhiều companion skills khi repo signal chưa đủ rõ
- Để workspace-local skills sống mãi dù repo đã bỏ runtime/feature đó
- Không có `when not to use` nên companion skill bị load tràn lan

## Evolution Policy

- Companion skill nên có phần `when not to use`
- Companion skill nên có repo signals rõ
- Workspace nên có smoke tests cho routing nếu có nhiều local skills
- Khi runtime/feature bị bỏ, retire hoặc archive companion skill tương ứng
- Giữ local skill mỏng: repo-specific heuristics, không lặp lại orchestration của Forge
- Giữ `AGENTS.md` ổn định và mỏng; routing detail nên dồn về workspace map
- Khi routing đổi, update workspace map trước rồi mới update entrypoint docs nếu cần
- Sau khi đổi router docs hoặc local skill inventory, chạy `scripts/check_workspace_router.py`

## Quick Checklist

- [ ] Runtime được xác định từ artifact thật
- [ ] Forge vẫn giữ verification/evidence/reporting
- [ ] Companion chỉ thêm stack-specific detail
- [ ] Không có rule chồng chéo hoặc mâu thuẫn
- [ ] User-facing activation line nói rõ companion skill nào đang được dùng
