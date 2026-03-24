# Forge Core vs Adapters Plan

**Status:** In progress  
**Date:** 2026-03-24  
**Input backlog:** [2026-03-23-forge-vs-awf-gap-backlog.md](C:/Users/Admin/.gemini/LamDiFood/docs/plans/2026-03-23-forge-vs-awf-gap-backlog.md)  
**Goal:** bóc backlog AWF-centric thành kế hoạch triển khai đúng kiến trúc `forge-core + forge-antigravity + forge-codex`  
**Non-goal:** không port nguyên xi UX của AWF sang mọi host, không nhét host-specific ceremony vào `forge-core`

**Design constraint:** `forge-core` phải đủ sạch để sau này thêm adapter mới như `forge-claude` mà không cần viết lại câu chuyện lõi của Forge.

---

## 1. Nguyên tắc tách lớp

### `forge-core` chỉ nên giữ

- capability dùng được trên cả Antigravity và Codex
- capability dùng được hoặc chỉ cần chỉnh rất mỏng cho adapter tương lai như `forge-claude`
- registry, routing, verification, repo-state reasoning
- workflow logic không phụ thuộc một host command surface cụ thể
- schema và engine cho personalization, nếu behavior đó có thể dùng chung

### `forge-antigravity` nên giữ

- slash/wrapper surface gần với AWF để giảm friction cho user hiện tại
- metadata và instruction surface riêng của Antigravity
- compatibility aliases cho luồng dùng hằng ngày của Antigravity
- onboarding thiên về người dùng Forge/AWF cũ

### `forge-codex` nên giữ

- AGENTS-oriented instruction surface
- wrapper mỏng, ít command alias hơn Antigravity
- mapping phù hợp với thói quen natural-language + repo-state của Codex
- chỉ giữ alias nào thực sự giúp, không bê cả AWF UX sang

---

## 2. Quy tắc quyết định

Mỗi backlog item được xếp vào một trong bốn nhóm:

1. `Core cho cả hai`
2. `Core engine + adapter wrapper`
3. `Adapter-specific`
4. `Defer`

Ưu tiên:

1. thêm engine dùng chung trước
2. thêm Antigravity wrapper trước nếu item chủ yếu giải quyết gap AWF migration
3. chỉ thêm Codex wrapper khi nó vẫn hợp với UX tự nhiên của Codex
4. không tạo workflow mới nếu chỉ là alias mỏng trên capability đã có

Hard gate:

- nếu một item không vượt qua bài test `future forge-claude adapter`, mặc định không được vào `forge-core`

---

## 3. Decision Matrix

| Item | Phân loại | `forge-core` | `forge-antigravity` | `forge-codex` | Quyết định |
|------|-----------|--------------|----------------------|----------------|-----------|
| P0.1 Preferences + adaptive language | Core engine + adapter wrapper | Đã có schema + resolver cho `technical_level`, `detail_level`, `autonomy_level`, `personality` | Đã nối host entrypoint vào core engine; wrapper `/customize` để sau | Đã nối AGENTS/adapter entrypoint vào core engine; customize flow để sau | Delivered ở core + thin adapter wiring |
| P0.2 `/help` + `/next` | Core engine + adapter wrapper | Đã có navigator logic đọc repo state, plans, docs, `.brain` khi cần | Đã nối adapter vào core navigator; slash wrapper dày hơn để sau | Đã nối AGENTS guidance vào core navigator; natural-language first giữ nguyên | Delivered ở core + thin adapter wiring |
| P0.3 `/run` | Core cho cả hai | Đã có `run_with_guidance.py` + workflow `run` host-neutral: chạy command, đọc output, route tiếp sang debug/test/deploy | Adapter Antigravity chỉ thêm wrapper `/run` trên contract của core | Adapter Codex giữ natural-language first trên contract của core | Delivered ở core + thin adapter wiring |
| P1.1 Error translator | Core cho cả hai | Đã có helper + script `translate_error.py` dùng chung cho `run/build/debug/test`, kèm sanitation và pattern database host-neutral | Không cần logic riêng | Không cần logic riêng | Delivered ở core |
| P1.2 `/bump` | Core engine + adapter wrapper | Đã có `prepare_bump.py` + workflow `bump` cho semver math, VERSION/CHANGELOG update, và verification checklist | Adapter Antigravity chỉ thêm wrapper `/bump` trên contract của core | Adapter Codex expose qua natural language hoặc alias nhẹ | Delivered ở core + thin adapter wiring |
| P1.3 `/rollback` | Core engine + adapter wrapper | Đã có `resolve_rollback.py` + workflow `rollback` cho scope/risk framing và recovery strategy | Adapter Antigravity chỉ thêm wrapper `/rollback` trên contract của core | Adapter Codex expose rollback flow qua natural language hoặc alias nhẹ | Delivered ở core + thin adapter wiring |
| P1.4 `/init` + onboarding mỏng | Tách đôi | Core chỉ nên có workspace skeleton logic nếu thật sự reusable | Onboarding và first-run prompt nên làm ở adapter này trước | Codex chỉ nên có `init` tối thiểu, không cần onboarding dày | Antigravity-first |
| P2.1 `/customize` đầy đủ | Core engine + adapter wrapper | Mở rộng preferences schema + persistence | Q&A flow đầy đủ hơn | Flow ngắn hơn, ít ceremony hơn | Làm sau P0.1 |
| P2.2 Session ergonomics wrappers | Adapter-specific trên core session | Không đổi logic session lõi, chỉ giữ API/contract rõ | Thêm wrapper restore/save/help thuận tay hơn | Thêm wrapper tối giản, không làm Codex nặng ceremony | Antigravity-first |
| P2.3 Compatibility aliases | Adapter-specific | Không nên vào core | Có giá trị cao vì user đang chuyển từ AWF | Chỉ giữ alias thật cần, không copy cả bộ AWF | Antigravity-first, Codex selective |
| P2.4 Self-update workflow | Defer / platform-specific | Không nên vào core lúc này | Có thể làm sau nếu thật sự cần | Có thể làm sau nếu thật sự cần | Defer |

---

## 4. Bản bóc tách đúng hơn theo package

### Wave A - Core foundation

Mục tiêu: thêm capability dùng chung mà không làm core AWF-shaped.

Phạm vi:

- preferences schema + response-style resolver
- help/next navigator engine
- run workflow
- bump workflow
- rollback workflow
- error translator helper

Kỳ vọng file-level:

- `packages/forge-core/workflows/operator/help.md`
- `packages/forge-core/workflows/operator/next.md`
- `packages/forge-core/workflows/operator/run.md`
- `packages/forge-core/workflows/operator/bump.md`
- `packages/forge-core/workflows/operator/rollback.md`
- `packages/forge-core/data/` thêm preferences schema nếu cần
- `packages/forge-core/scripts/` chỉ thêm script khi deterministic verification thật sự có ích

Ghi chú:

- `help/next` nên đọc repo state trước, không biến thành recap theater
- `run` phải report command + output chính + next step, không chỉ nói "đã chạy"
- `bump` và `rollback` là delivery workflows, không phải host gimmick

### Wave B - Antigravity adapter

Mục tiêu: giảm friction cho user AWF/Antigravity hiện tại.

Phạm vi:

- slash surfaces rõ cho `/help`, `/next`, `/run`, `/bump`, `/rollback`
- `/customize` sớm ngay sau khi core có preferences engine
- onboarding mỏng / init-first experience
- session wrappers tiện tay hơn
- compatibility aliases từ AWF nơi có giá trị thật

Nên giữ:

- trải nghiệm "operator-friendly"
- wrapper mỏng trên core capability

Không nên làm:

- fork logic của core
- tạo một bộ standards song song chỉ để giống AWF

### Wave C - Codex adapter

Mục tiêu: áp dụng cùng capability nhưng theo UX hợp Codex hơn.

Phạm vi:

- cập nhật `AGENTS.example.md` để chỉ rõ natural-language entrypoints cho `help/next/run/bump/rollback/customize`
- chỉ thêm alias nào thật sự giảm friction
- tận dụng `AGENTS.md` + repo state thay vì slash-heavy interaction

Nên giữ:

- natural-language first
- thin wrapper
- repo-first, instruction-light

Không nên làm:

- bê nguyên command grammar của AWF
- onboarding dài dòng
- session/save wrappers nặng hơn bản core

---

## 5. Recommendation theo host

### Antigravity

Nên nhận gần như toàn bộ backlog, nhưng theo thứ tự:

1. Preferences + `/customize`
2. `/help` + `/next`
3. `/run`
4. `/bump` + `/rollback`
5. `init` + onboarding mỏng
6. session wrappers
7. compatibility aliases

Lý do:

- user base ở đây gần AWF nhất
- adapter này đang là bản production chính
- lợi ích lớn nhất đến từ wrapper UX, không phải từ thay đổi orchestration core

### Codex

Nên nhận phiên bản chọn lọc:

1. preferences engine
2. `help/next`
3. `run`
4. `bump`
5. `rollback`
6. customize flow ngắn

Chưa nên ưu tiên:

- onboarding dày
- compatibility aliases kiểu AWF đầy đủ
- session wrapper dày
- self-update workflow

Lý do:

- Codex vốn đã mạnh ở natural-language + repo-state reasoning
- UX đúng cho Codex là "mỏng và rõ", không phải "nhiều command"

---

## 6. Những thứ nên sửa trong backlog cũ

Backlog ngày 2026-03-23 vẫn hữu ích, nhưng đang AWF-centric ở ba điểm:

1. dùng slash command làm đơn vị thiết kế chính
2. xem mọi improvement như nên có cho cùng một bundle
3. chưa tách rõ engine dùng chung với wrapper riêng từng host

Phiên bản mới nên đổi framing thành:

- `core capability`
- `Antigravity wrapper`
- `Codex wrapper`
- `defer`

---

## 7. Kết luận thực dụng

Nếu chỉ chọn một hướng đúng nhất:

- làm `Wave A` ở `forge-core`
- rollout wrapper đầy đủ trước ở `forge-antigravity`
- rollout wrapper chọn lọc ở `forge-codex`

Tức là:

- đừng phát triển hai backlog riêng biệt
- cũng đừng ép hai adapter phải giống nhau
- hãy làm một core mạnh hơn, rồi để mỗi host có UX bề mặt riêng

---

## 8. Next step đề xuất

1. Chốt matrix này làm source-of-truth mới.
2. Tách backlog implementation thành 3 nhóm issue:
   - core
   - antigravity
   - codex
3. Làm Wave A trước.
4. Sau khi Wave A pass verify, triển khai wrapper Antigravity.
5. Sau khi Antigravity ổn, mới thêm wrapper chọn lọc cho Codex.

---

## 9. Status Update - 2026-03-24

Wave A đã delivered ở `forge-core`.

Wave B đã delivered ở `forge-antigravity` theo đúng boundary:

- thêm bề mặt rõ ràng cho `/help`, `/next`, `/run`, `/bump`, `/rollback`
- thêm `/customize` trên core preferences schema + persistence (`resolve_preferences.py` + `write_preferences.py`)
- thêm `/init` trên core workspace bootstrap (`initialize_workspace.py`)
- thêm session ergonomics wrappers: `/recap`, `/save-brain`, `/handover`
- thêm compatibility layer giảm friction migration từ AWF/Antigravity cũ

Phần được thêm vào `forge-core` để hỗ trợ Wave B nhưng vẫn host-neutral:

- mở rộng preferences schema với `pace` và `feedback_style`
- thêm persistence helper cho preferences
- thêm reusable workspace skeleton init

Wave C đã delivered ở `forge-codex` theo đúng boundary:

- thêm thin wrappers cho `help`, `next`, `run`, `bump`, `rollback`, `customize`, và `init`
- giữ natural-language first, coi slash chỉ là alias optional
- cập nhật `AGENTS.example.md` để workspace Codex đưa về Forge mà không duplicate orchestration rules
- bổ sung release tests để build/install giữ nguyên Codex overlay surface

Không thêm cho Codex:

- `recap`, `save-brain`, `handover`
- onboarding dai dong
- compatibility alias day dac theo kieu AWF cu
