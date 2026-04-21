# Plan: Brainstorm v2 + Flat Build Routing

Status: implemented in `codex/flat-routing-model`

## Problem Statement

```text
For: Solo developer dùng Forge
Who: Không muốn Forge tách nhánh theo low/medium/high-risk trước khi build
That: Giữ một behavioral build chain phẳng, bỏ `spec-review` như stage active,
      nhưng không làm mất checkpoint trước build
```

## Chosen Direction

Áp dụng mô hình flat cho behavioral BUILD routing:

- Không chèn `spec-review` theo boundary risk nữa.
- Không chọn `implementer-spec-quality` nữa.
- Không bật `secure` chỉ vì auth/payment/migration keywords trong BUILD.
- Chuyển readiness checkpoint vào `brainstorm`, `plan`, `architect`, và `build`.
- Giữ tương thích đọc artifact cũ từ `.forge-artifacts/spec-review`, nhưng normalize về flat chain `plan -> build`.

## Implemented Changes

### Brainstorm v2

- `brainstorm.md` có `Flat Readiness Checkpoint`.
- Handoff sang `plan` phải nêu tradeoff, boundary assumptions, first proof, và reversal signal.
- Nếu boundary/security/migration/auth/payment/public-interface/compatibility còn mơ hồ, Brainstorm không được đẩy rủi ro xuống Build; phải hỏi một câu quyết định hoặc nâng từ `discovery-lite` lên `discovery-full`.

### Routing / Registry

- Active BUILD chain còn `brainstorm? -> plan -> architect? -> build -> test -> self-review -> quality-gate`.
- `orchestrator-registry.json` không còn `spec_review_gate`, `spec-review` stage, `implementer-spec-quality`, `spec-reviewer`, `requires_spec_review`, hoặc spec-review loop cap.
- `route_risk.py` chỉ còn Brainstorm gate logic; spec-review insertion logic đã bị gỡ.
- `track_execution_progress.py` chỉ còn lane `navigator`, `implementer`, `quality-reviewer`, và `deploy-reviewer`.

### State / Compatibility

- `record_spec_review_state.py` đã bị xóa khỏi active script surface.
- Legacy `.forge-artifacts/spec-review/.../latest.json` vẫn bootstrap được qua `legacy-spec-review-state`.
- Canonical workflow-state không còn giữ `latest_spec_review`.
- Legacy chain `plan -> spec-review -> build` được normalize thành `plan -> build`.

### Docs / Overlays

- Xóa `packages/forge-core/workflows/design/spec-review.md`.
- Cập nhật `brainstorm`, `plan`, `architect`, `build`, `review`, execution-delivery, help/next, reference-map, smoke checklist, core skill, Codex overlay, và Antigravity overlay.
- Gỡ locale overlay `spec_review_gate` cho Codex và Antigravity.
- Sửa Antigravity overlay locale test harness để chạy được từ source repo.

## Verification Plan

Các check cần chạy trước khi release hoặc merge:

```powershell
python -m unittest discover -s packages/forge-core/tests -p "test_contracts.py" -v
python -m unittest discover -s packages/forge-core/tests -p "test_route_preview.py" -v
python -m unittest discover -s packages/forge-core/tests -p "test_route_matrix.py" -v
python -m unittest discover -s packages/forge-core/tests -p "test_record_stage_state.py" -v
python -m unittest discover -s packages/forge-core/tests -p "test_help_next_workflow_state.py" -v
python packages/forge-codex/overlay/tests/test_adapter_locales.py
python packages/forge-antigravity/overlay/tests/test_adapter_locales.py
```

## Completion Criteria

- Active routing không còn `spec-review`.
- Registry không còn residual active spec-review references.
- Brainstorm v2 giữ checkpoint phẳng cho mọi behavioral BUILD risk.
- Legacy spec-review artifact vẫn resume/next được nhưng không tái tạo stage cũ.
- Codex và Antigravity overlay locale behavior cùng khẳng định Vietnamese risk keywords không kích hoạt pre-build review fork.
