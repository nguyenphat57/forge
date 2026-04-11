# Solo-Dev Opinionated Profile Spec

## Mục tiêu

Forge phải chuyển từ một tập workflow mạnh nhưng rời rạc sang một state machine rõ ràng cho solo dev:

- Có profile mặc định rõ: `solo-internal` và `solo-public`
- Mọi non-operator workflow phải có activation class rõ
- Mọi stage phải có trạng thái `completed`, `skipped`, hoặc `blocked`
- Không còn skip ngầm hoặc phụ thuộc quá nhiều vào agent suy diễn mềm
- `spec-review` là risk-gate, không phải size-gate
- `brainstorm` hấp thụ luôn discovery, mặc định bằng `discovery-lite`

## Phạm vi Profile

### Profile 1: `solo-internal`

Dùng khi:

- Sản phẩm chủ yếu phục vụ nội bộ
- Không có tín hiệu public release
- Deploy vào môi trường dùng thật nhưng không public rộng

### Profile 2: `solo-public`

Dùng khi có một trong các tín hiệu sau:

- Deploy production cho người dùng ngoài
- Prompt chứa `public`, `publish`, `external users`, `launch`
- Workspace/repo có cờ cấu hình public release

Profile phải được resolve và persist vào workflow-state, không để agent tự ngầm hiểu.

## Nguyên tắc Thiết Kế

- `small` được nhanh, nhưng không được vượt qua boundary risk
- Mọi boundary risk có quyền kéo `spec-review`, `secure`, `review-pack` vào
- Activation phải dựa trên rule và state, không dựa chủ yếu vào trực giác của agent
- Mọi stage phải có lý do kích hoạt hoặc lý do bỏ qua

## Workflow Map

### Feature / Greenfield / Internal

```text
brainstorm(discovery-lite -> discovery-full?) -> plan -> visualize? -> architect? -> spec-review? -> change? -> build -> test -> review-pack? -> self-review -> secure? -> verify-change? -> quality-gate -> release-doc-sync? -> deploy -> adoption-check?
```

### Feature / Greenfield / Public

```text
brainstorm(discovery-lite -> discovery-full?) -> plan -> visualize? -> architect? -> spec-review? -> change? -> build -> test -> review-pack -> self-review -> secure -> verify-change? -> quality-gate -> release-doc-sync -> release-readiness -> deploy -> adoption-check
```

### Debug

```text
debug -> plan? -> spec-review? -> build -> test -> self-review -> quality-gate -> deploy?
```

### Refactor

```text
refactor -> test -> self-review -> quality-gate?
```

### UI Feature

```text
brainstorm? -> plan -> visualize -> architect? -> spec-review? -> build -> test -> self-review -> quality-gate -> deploy?
```

## Activation Matrix

| Workflow | Activation class | solo-internal | solo-public |
| --- | --- | --- | --- |
| `brainstorm` | default | New feature, greenfield, direction mơ hồ | Same |
| `plan` | default | Mọi BUILD/DEBUG không trivial | Same |
| `visualize` | risk-gated | UI medium+, đổi interaction model, touch/dense-data flow | Same |
| `architect` | risk-gated | Đổi data/auth/state/system shape | Same |
| `spec-review` | risk-gated | Mọi size nếu boundary risk hoặc packet chưa rõ | Same |
| `change` | state-gated | Chỉ nên bật khi task dài, pause/resume, multi-slice | Same |
| `build` | default | Sau khi proof-before-progress được khóa | Same |
| `test` | default | Luôn chạy sau build | Same |
| `review-pack` | state-gated | Trước deploy vào shared env dùng thật | Trước mọi release thật |
| `self-review` | default | Bắt buộc cho medium+ và mọi deploy candidate | Same |
| `secure` | risk-gated | Auth/payment/data/integration/shared secret | Bắt buộc cho release-sensitive flow |
| `verify-change` | state-gated | Chỉ khi có change artifact | Same |
| `quality-gate` | default gate | Bắt buộc cho medium+ và mọi deploy candidate | Same |
| `release-doc-sync` | state-gated | Chỉ khi shared env release đổi config/schema/product surface | Bắt buộc khi release surface đổi |
| `release-readiness` | state-gated | Chỉ critical internal release | Bắt buộc cho public production hoặc public release nhạy cảm |
| `deploy` | explicit end stage | Explicit ship step | Explicit ship step |
| `adoption-check` | state-gated | Sau deploy vào shared env | Sau release public/shared |

## Activation Rules Cập Nhật

### `brainstorm` với `discovery-lite/full`

`brainstorm` là entry workflow mặc định cho:

- Greenfield feature
- Feature có direction mơ hồ
- Task có từ 2 hướng tiếp cận trở lên
- UI/UX shape chưa khóa

#### Mode mặc định: `discovery-lite`

`brainstorm` luôn bắt đầu bằng `discovery-lite`.

`discovery-lite` phải khóa đủ 7 điểm:

1. Actor là ai
2. Pain hoặc job-to-be-done là gì
3. Desired outcome là gì
4. Minimal success signal là gì
5. Constraint quan trọng nào đang ràng buộc
6. Non-goals là gì
7. First proof để kiểm tra hướng là gì

Chỉ sau khi đủ 7 điểm này, `brainstorm` mới được so sánh option và chốt direction.

#### Escalation sang `discovery-full`

`brainstorm` phải tự nâng lên `discovery-full` nếu có một trong các tín hiệu:

- Discovery-lite vẫn chưa đủ để viết problem statement an toàn
- Có nhiều actor có nhu cầu xung đột
- Current workflow chưa rõ
- Cost of wrong direction cao
- Process flow hoặc UX flow là phần cốt lõi của bài toán

`discovery-full` bổ sung:

- Current workflow map
- Pain ranking
- Failure và edge scenarios
- Assumptions cần validate
- Success signal mạnh hơn

#### Output rule

`brainstorm` chỉ được kết thúc ở một trong hai trạng thái:

- `direction-locked`
- `decision-blocked`

Không có trạng thái mơ hồ ở giữa.

### `spec-review` theo risk thay vì size

`spec-review` không còn là size-gate. Nó là `risk + packet clarity gate`.

`spec-review` bật mặc định cho:

- Mọi `large` build

`spec-review` bật cho mọi size nếu có `boundary risk`, gồm:

- Auth hoặc permission
- Payment hoặc billing
- Schema, migration, backfill
- Public hoặc external interface
- Integration, webhook, consumer dependency
- Offline, concurrency, state sync
- Rollback khó

`spec-review` cũng bật cho mọi size nếu packet thiếu một trong các mục:

- Source of truth
- First slice
- File hoặc surface scope
- Baseline proof
- Proof before progress
- Reopen conditions

Không được vào `build` khi `spec-review` đang là required mà chưa có quyết định `go`.

## Chain Solo-Dev Cuối Cùng

### Default chain: `solo-internal`

```text
brainstorm(discovery-lite -> discovery-full?) -> plan -> visualize? -> architect? -> spec-review? -> change? -> build -> test -> review-pack? -> self-review -> secure? -> verify-change? -> quality-gate -> release-doc-sync? -> deploy -> adoption-check?
```

### Default chain: `solo-public`

```text
brainstorm(discovery-lite -> discovery-full?) -> plan -> visualize? -> architect? -> spec-review? -> change? -> build -> test -> review-pack -> self-review -> secure -> verify-change? -> quality-gate -> release-doc-sync -> release-readiness -> deploy -> adoption-check
```

## Phần Triển Khai Chi Tiết

Các phần sau được tách sang appendix để giữ spec chính gọn và đúng quy ước:

- Rule hóa activation
- State hóa artifact và gate
- Artifact transitions
- Giảm chỗ agent tự suy diễn mềm
- Patch plan
- Tiêu chí hoàn thành

Xem tiếp tại:

- `docs/specs/2026-03-31-solo-dev-opinionated-profile-spec-appendix.md`
- `docs/plans/2026-03-31-solo-dev-opinionated-profile-implementation-checklist.md`
