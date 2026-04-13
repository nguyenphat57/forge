# Plan: Forge Build Chain End-to-End State Machine

Status: implemented

## Summary

Biến `workflow-state` thành canonical state root cho build chain `brainstorm -> plan -> visualize -> architect -> spec-review -> build -> test -> self-review -> secure -> quality-gate -> deploy`.

Các quyết định đã khóa:
- `workflow-state` là single source of truth
- dùng `generic stage-state recorder`
- `docs/plans` và `docs/specs` chỉ là human sidecar
- giữ `hard cutover`
- không dùng runtime fallback
- thêm bootstrap/migration step để seed machine root trước cutover
- compatibility projections giữ ngắn hạn như derived fields

## Key Changes

- Chuẩn hóa `workflow-state/latest.json` thành machine root với tối thiểu:
  - `schema_version`
  - `required_stage_chain`
  - `current_stage`
  - `stages`
  - `last_transition`
  - `summary`
  - các projections legacy còn cần cho read-model/tests
- Spec rõ `stages` ledger:
  - mỗi stage có `status`, `recorded_at`, `transition_id`, `source_path/event_ref`
  - stage-specific fields:
    - `plan`, `architect`: artifact refs
    - `build`, `test`: proof/evidence refs
    - `self-review`, `secure`, `quality-gate`: decision/disposition + evidence refs
    - `deploy`: target identity, release/artifact id, post-deploy verification, rollback path
- Thêm `record_stage_state.py` làm write surface chuẩn cho toàn build chain.
- Giữ `record_direction_state.py`, `record_spec_review_state.py`, `record_review_state.py`, `record_quality_gate.py` một release như thin wrappers sang generic recorder.
- Stage advancement chỉ được phép qua stage-state events hợp lệ.
- `run-report`, packet-index, docs, session, handover chỉ là evidence/read-model; không được tự advance lifecycle stage.
- `help`, `next`, `resume` chuyển sang đọc canonical machine root; bỏ inference từ `latest_plan/latest_spec`, session, handover, git heuristics.
- Loại bỏ nhánh rebuild active state từ `legacy-artifacts` sau cutover.
- Thêm bootstrap path:
  - nếu workspace có plan/spec hoặc legacy artifacts nhưng chưa có machine root, phải seed root trước
  - sau đó `help/next/resume` mới coi chain là active
- Thêm stale-write guard tối thiểu:
  - `transition_id`
  - `expected_previous_stage`
  - reject stale/invalid transition thay vì last-write-wins im lặng

## Test Plan

- Happy path:
  - seed small chain `plan -> build -> test -> quality-gate`
  - seed full release-sensitive chain đến `deploy`
  - verify advance đúng khi stage `completed` hoặc `skipped`
- Non-happy path:
  - `spec-review revise`
  - `quality-gate blocked`
  - `secure blocked`
  - `deploy failed` với rollback path
- Cutover:
  - có `docs/plans` nhưng chưa seed machine root -> `unscoped`
  - session/handover không override machine root
  - legacy artifacts không còn rebuild thành active state
  - bootstrap seed đúng machine root cho workspace cũ
- Robustness:
  - empty `required_stage_chain`
  - partial/corrupt `latest.json`
  - stale merge-ready filter vẫn đúng
  - reject stale transition khi `expected_previous_stage` không khớp

## Important Interface Changes

- Thêm `record_stage_state.py`
- `workflow-state/latest.json` đổi schema và bắt đầu từ `schema_version: 1`
- `help`, `next`, `resume` không còn coi docs/session/handover là lifecycle truth
- `secure` và `deploy` trở thành first-class machine stages trong root canonical

## Assumptions

- Không redesign operator surface ở tranche này
- `post-deploy verification` vẫn nằm trong `deploy`, chưa tách stage mới
- `rollback` vẫn là recovery path của `deploy failed`, chưa thành stage riêng
- `DEBUG`, `OPTIMIZE`, `SESSION` chỉ cập nhật consumer/read-model cần thiết để không đọc sai root mới
- Nếu cần phased rollout mềm hơn, đó là tranche sau; tranche này ưu tiên khóa single source of truth trước
