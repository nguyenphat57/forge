# Brainstorm Plan: Nâng Build Chain Forge Thành End-to-End State Machine

Status: implemented

## Summary

Nâng cấp này sẽ biến `workflow-state` thành canonical state root cho toàn bộ build chain `brainstorm -> plan -> visualize -> architect -> spec-review -> build -> test -> self-review -> secure -> quality-gate -> deploy`, thay vì tiếp tục suy luận stage từ nhiều nguồn như `docs/plans`, `.brain/session.json`, handover, và git state.

Hướng được khóa:
- Ưu tiên `kín state trước`
- Chọn `hard cutover sớm`
- `workflow-state` là nguồn truth chuẩn
- `docs/plans` và `docs/specs` chỉ là human sidecar, không còn quyết định stage
- Dùng `generic stage-state` thay cho việc tiếp tục nở thêm recorder riêng từng stage

## Key Changes

### 1. Canonical State Root

- Chuẩn hóa `workflow-state/latest.json` thành machine root versioned, chứa tối thiểu:
  - `required_stage_chain`
  - `current_stage`
  - `stages`
  - `last_transition`
  - `summary`
  - các compatibility projections còn cần giữ ngắn hạn
- `current_stage` chỉ được tính từ stage ledger trong machine root; không còn lấy từ `latest_plan`, `latest_spec`, session, hay git heuristics.
- `events.jsonl` tiếp tục giữ vai trò transition log; `packet-index.json` vẫn là read-model rẻ, không phải source-of-truth.

### 2. Generic Stage-State Contract

- Thêm một recorder chung, ví dụ `record_stage_state.py`, làm entrypoint ghi state cho mọi stage trong build chain.
- Mỗi stage event phải mang:
  - `stage`
  - `stage_status`
  - `profile`
  - `intent`
  - `required_stage_chain`
  - `activation_reason` hoặc `skip_reason`
  - `artifact_refs`
  - `decision/disposition` khi applicable
  - `next_stage_override` khi không đi theo happy path
  - `summary`, `notes`, `next_actions`
- Typed requirements theo stage:
  - `plan` và `architect` bắt buộc có artifact path/ref, nhưng artifact đó là sidecar cho người đọc
  - `build` và `test` bắt buộc có proof/evidence refs
  - `self-review`, `secure`, `quality-gate` bắt buộc có decision/disposition + evidence refs
  - `deploy` bắt buộc có target identity, gate summary, artifact/release id, post-deploy verification, rollback path

### 3. Transition Rules

- `route-preview` hoặc explicit machine init là cách duy nhất để seed `required_stage_chain`.
- Stage `completed` hoặc `skipped` sẽ advance sang stage kế tiếp không bị skip trong chain.
- Stage `blocked` giữ machine tại stage hiện tại.
- Các nhánh không-happy-path như `spec-review: revise`, `quality-gate: blocked`, `secure: blocked`, `deploy: failed` phải ghi explicit `next_stage_override`; không còn để `help/next` tự suy luận ngược.
- `run-report` và các output kiểm thử chỉ là evidence sidecars; stage advancement chỉ xảy ra khi có stage-state event hợp lệ.

### 4. Hard Cutover Cho Help/Next/Session

- `resolve_help_next.py` và `session_context.py` chuyển sang đọc machine root làm nguồn truth duy nhất cho active chain.
- Bỏ inference kiểu:
  - có `docs/plans/*.md` thì coi là `planned`
  - có session/handover thì coi như active chain nếu machine không xác nhận
- Sau cutover, `docs/plans` và `docs/specs` chỉ còn được hiển thị như evidence/path refs trong response.
- `.brain/session.json` và `.brain/handover.md` giữ vai trò continuity note, không còn quyết định lifecycle stage.

### 5. Compatibility Và Migration

- Giữ `record_direction_state.py`, `record_spec_review_state.py`, `record_review_state.py`, `record_quality_gate.py` trong một release như thin wrappers trên generic recorder để tránh gãy surface nội bộ.
- Không thêm recorder riêng mới cho `plan`, `architect`, `secure`, `deploy`; các stage này đi thẳng vào generic stage-state.
- Compatibility projections như `latest_direction`, `latest_spec_review`, `latest_review`, `latest_gate` có thể còn giữ ngắn hạn để không làm gãy test/read-model, nhưng phải được xem là derived, không phải canonical.
- Scope của tranche này là build chain từ `brainstorm` đến `deploy`; `DEBUG`, `OPTIMIZE`, `SESSION` chỉ cập nhật phần consumer/read-model cần thiết để không đọc sai root mới.

## Important Interface Changes

- Thêm generic stage-state CLI/script làm machine write surface chuẩn.
- `workflow-state/latest.json` đổi schema để chứa stage ledger canonical.
- `help`, `next`, `resume` ngừng coi `docs/plans` và `docs/specs` là nguồn stage state.
- `deploy` stage được first-class hóa trong machine root, thay vì chỉ mạnh ở workflow prose/gate semantics.

## Test Plan

- Small chain:
  - seed chain `plan -> build -> test -> quality-gate`
  - ghi `plan completed` với artifact ref
  - advance đúng sang `build`, rồi `test`, rồi `quality-gate`
- Medium/large release-sensitive chain:
  - seed full chain đến `deploy`
  - `self-review -> secure -> quality-gate -> deploy` phải advance đúng theo stage events
- Hard cutover behavior:
  - repo có `docs/plans/*.md` nhưng không có machine root phải ra `unscoped`, không còn tự ra `planned`
  - session/handover không được override machine root
- Non-happy-path transitions:
  - `spec-review revise` phải giữ machine blocked và yêu cầu `next_stage_override`
  - `quality-gate blocked` phải giữ machine ở gate hoặc quay explicit về stage được chỉ định
  - `deploy failed` phải ghi rollback path và không tự coi là complete
- Compatibility:
  - các dedicated wrappers cũ phải sinh ra stage events tương đương generic contract
  - stale merge-ready filtering vẫn đúng sau khi chuyển sang root mới
- Validation:
  - reject event thiếu required fields theo stage
  - reject invalid transition ngoài chain nếu không có override hợp lệ

## Assumptions And Defaults

- Tranche này không redesign operator surface; giữ `help/next/run/...` như cũ, chỉ thay engine state bên dưới.
- `post-deploy verification` được model bên trong `deploy` stage, chưa tách thành stage mới.
- `rollback` chưa thành stage chính trong chain này; vẫn là recovery path/reference được ghi vào deploy failure state.
- `docs/plans` và `docs/specs` vẫn được duy trì cho con người, nhưng machine chỉ giữ path/ref tới chúng.
- Sau khi machine root ổn định, mới xét tranche tiếp theo để gom nốt các quality/read-model projections cũ.
