# Solo-Dev Opinionated Profile Spec Appendix

## Rule Hóa Activation

Router phải xuất `required_stages`, không chỉ xuất danh sách skill.

Mỗi stage phải có `activation_reason` từ enum:

- `default_chain`
- `greenfield_feature`
- `ui_medium_plus`
- `interaction_model_change`
- `boundary_risk`
- `packet_unclear`
- `shared_env_release`
- `public_release`
- `change_artifact_present`
- `critical_internal_release`

Mỗi stage chỉ được `skipped` với `skip_reason` từ enum:

- `non_ui`
- `direction_locked`
- `packet_clear`
- `low_risk_boundary`
- `no_change_artifact`
- `no_shared_env`
- `no_release_surface`
- `not_public_release`

`quality-gate` chỉ được `go` nếu toàn bộ required stage trước đó đều:

- `completed`
- hoặc `skipped` với lý do hợp lệ

## State Hóa Artifact Và Gate

Stage status chuẩn:

- `pending`
- `required`
- `active`
- `completed`
- `skipped`
- `blocked`

Gate decision chuẩn:

- `go`
- `revise`
- `blocked`

Workflow-state mẫu:

```json
{
  "profile": "solo-internal",
  "intent": "BUILD",
  "current_stage": "plan",
  "stages": {
    "brainstorm": {
      "status": "completed",
      "mode": "discovery-lite",
      "activation_reason": "greenfield_feature",
      "artifact": ".forge-artifacts/direction/<slug>/latest.json"
    },
    "visualize": {
      "status": "skipped",
      "skip_reason": "non_ui"
    },
    "spec-review": {
      "status": "required",
      "activation_reason": "boundary_risk"
    },
    "quality-gate": {
      "status": "pending"
    }
  }
}
```

## Artifact Transitions

- `brainstorm` -> direction brief
- `plan` -> implementation-ready packet
- `visualize` -> visual brief
- `architect` -> design hoặc ADR-lite
- `spec-review` -> readiness decision artifact
- `change` -> active change folder
- `build` -> execution checkpoint
- `test` -> verification artifact
- `self-review` -> review state
- `review-pack` -> pre-release checklist
- `quality-gate` -> gate record
- `release-doc-sync` -> docs drift report
- `release-readiness` -> readiness verdict
- `deploy` -> deploy report
- `adoption-check` -> adoption check record

## Giảm Chỗ Agent Tự Suy Diễn Mềm

Các quyết định sau không được để agent tự cảm nhận mềm:

- Task nhỏ có được skip `spec-review` hay không
- Release nội bộ có cần `review-pack` hay không
- Packet đã đủ rõ để code hay chưa
- Có cần `visualize` cho UI change hay không
- Có cần `release-doc-sync` hay `release-readiness` hay không

Các quyết định này phải đi qua:

- Risk categories
- Packet checklist
- Release target classification
- Persisted workflow-state

`route_preview` phải hiển thị:

- Profile
- Exact chain
- Required stages
- Activation reasons
- Skip reasons

## Patch Plan

### Routing Và Registry

Sửa:

- `packages/forge-core/data/orchestrator-registry.json`
- `packages/forge-core/scripts/route_analysis.py`
- `packages/forge-core/scripts/route_risk.py`
- `packages/forge-core/scripts/route_process_requirements.py`
- `packages/forge-core/scripts/route_preview.py`

Việc cần làm:

- Thêm `solo_profiles`
- Thêm `activation_reasons`
- Thêm `skip_reasons`
- Thêm `shared_env_rules`
- Thêm `release_surface_rules`
- Tách chain cho `solo-internal` và `solo-public`
- Resolve profile trước khi build chain
- Render `required_stages` thay vì chỉ render `skills`

### Workflow Docs

Sửa:

- `workflows/design/brainstorm.md`
- `workflows/design/spec-review.md`
- `workflows/design/visualize.md`
- `workflows/execution/review.md`
- `workflows/execution/review-pack.md`
- `workflows/execution/release-doc-sync.md`
- `workflows/execution/release-readiness.md`

Thêm mới:

- `workflows/execution/adoption-check.md`

### Scripts Và Artifact Recording

Thêm scripts:

- `record_direction_state.py`
- `record_spec_review_state.py`
- `record_adoption_check.py`

Tái dùng workflow-state như spine chung, không để mỗi gate sống tách rời.

### Tests

Cập nhật:

- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_quality_gate.py`
- `packages/forge-core/tests/test_release_readiness.py`
- `packages/forge-core/tests/test_review_pack.py`

Thêm các cases bắt buộc:

- `small but boundary-risk -> spec-review`
- `UI medium+ -> visualize`
- `shared env internal deploy -> review-pack`
- `public prod -> release-readiness`
- `greenfield ambiguous -> brainstorm discovery-lite/full`

## Tiêu Chí Hoàn Thành

Forge được coi là đạt profile này khi:

- `brainstorm` thực sự hấp thụ discovery-lite/full
- `spec-review` được route theo risk, không phụ thuộc size
- `visualize`, `review-pack`, `release-doc-sync`, `release-readiness` không còn là workflow sống ngoài happy path
- `route_preview` hiển thị được chain, required stages, activation reasons, skip reasons
- `quality-gate` dựa trên state và artifacts thật, không dựa vào suy diễn mềm của agent
