# Brainstorm: Thin SKILL.md (Revised)

Date: 2026-04-11
Status: historical brainstorm

## Vấn đề

`SKILL.md` đang phình to theo thời gian. Mỗi feature mới thường thêm prose, table, hoặc listing vào `SKILL.md` thay vì cập nhật canonical registry hoặc references phù hợp.

Hiện trạng trên source tree, đo theo raw file bytes và newline count:

| File | Bytes | Lines |
|------|-------|-------|
| `forge-core/SKILL.md` | `22288` | `393` |
| `forge-codex/overlay/SKILL.md` | `24493` | `432` |
| `forge-antigravity/overlay/SKILL.md` | `26951` | `485` |

Điều này có hai hệ quả:

1. Agent phải nạp một bootstrap file dài ngay từ đầu thay vì chỉ nạp contract cần nhớ liên tục.
2. Nội dung policy bị copy giữa core và 2 adapter, nên mỗi thay đổi nhỏ đều có nguy cơ drift.

Current repo state: ba file vẫn còn đủ dài để không còn đúng tinh thần "bootstrap first".

## Nguyên nhân gốc

### Triple duplication giữa core và overlays

Ba `SKILL.md` hiện chia sẻ phần lớn nội dung policy:

- `Intent Detection`
- `Complexity Assessment`
- `Skill Composition Matrix`
- `How to load skills`
- `Verification Strategy`
- `Solo Profile And Workflow-State Contract`
- `Skill Registry`
- `Global Resilience`
- `Golden Rules`

Current repo state: các section này hoặc giống hệt, hoặc chỉ khác wording nhẹ giữa core, Codex, và Antigravity.

### Registry đã là canonical source cho phần lớn routing data

`data/orchestrator-registry.json` hiện đã chứa các mảnh dữ liệu mà `SKILL.md` đang lặp lại bằng prose hoặc bảng:

- intent families và chain order
- complexity contract
- stage status vocabulary
- skill-selection/footer contract
- host capability tiers

Current repo state: registry đã là source-of-truth cho test contracts quan trọng; `SKILL.md` chủ yếu đang đóng vai trò bản sao dễ drift.

### References đã chứa phần lớn prose tra cứu khi cần

Current references đã có các entrypoint phù hợp cho deep detail:

- `references/kernel-tooling.md` cho tooling surface kernel-only
- `references/error-translation.md` cho error translation rules
- `references/personalization.md` cho preference/personalization detail
- `references/reference-map.md` cho reading order và pointer sang references khác

Current repo state: `references/kernel-tooling.md` mới là current entrypoint cho tooling surface sau V3. Nếu tiếp tục mở thêm một tooling doc khác như current source ngang hàng, repo sẽ quay lại bài toán hai nguồn "current" cạnh tranh nhau.

### Build semantics hiện tại không hỗ trợ overlay delta-only

Current build flow cho adapter bundle là:

1. copy `forge-core` vào bundle đích
2. chạy `apply_overlay()`
3. file trùng tên trong overlay sẽ overwrite file tương ứng trong bundle

Current repo state: semantics này có nghĩa là nếu overlay `SKILL.md` chỉ chứa host delta, bundle ship ra sẽ mất shared bootstrap content của core. Nói cách khác, `delta-only overlay` chưa tương thích với build contract hiện tại.

## Giải pháp đề xuất: Thin-SKILL Contract-Only

Proposed direction: biến `SKILL.md` thành bootstrap contract ngắn gọn. Agent đọc `SKILL.md` để biết nguyên tắc ra quyết định và behavioral guardrails, không phải để tra inventory hay lookup table chi tiết.

Thin-SKILL nên tách nội dung thành 3 lớp rõ ràng:

### 1. Inline bootstrap

Phần phải ở lại trong `SKILL.md` vì agent cần nhớ liên tục:

- Golden Rules
- Iron Laws hoặc skill laws ngắn gọn
- Verification Strategy
- Skill Composition Matrix bản compact
- Skill loading procedure
- Independence Rule
- Host-specific protocol/operator delta
- pointer sang reference map

### 2. Delegate sang registry hoặc references

Phần không nên tiếp tục sống inline:

- intent keyword tables
- complexity threshold tables
- error translation catalog
- bundle layout tree
- tooling inventory chi tiết
- personalization detail dài
- resilience prose dài

Proposed direction: data sống ở registry; prose sống ở references; `SKILL.md` chỉ còn pointer có chủ đích.

### 3. Prerequisite kỹ thuật để adapter thin-SKILL khả thi

Đây là điểm phải khóa rõ:

- current build chưa hỗ trợ `core thin-SKILL + adapter delta-only SKILL`
- nếu muốn overlay chỉ chứa host delta thực sự, build phải sinh ra `generated merged SKILL artifact` cho từng adapter bundle
- nếu tranche hiện tại chưa đáng đầu tư merge semantics mới, vẫn có một fallback thực dụng: overlay tiếp tục overwrite `SKILL.md`, nhưng file overlay chỉ giữ `host delta + compact shared rules`

Vì vậy, recommendation của brainstorm này là:

- dài hạn: `Thin core + delta-only adapter + generated merge`
- ngắn hạn fallback: `Thin core + compact overwrite adapter`

Proposed direction: không để generated merge thành open question mơ hồ. Nó là target state rõ ràng; còn compact overwrite là fallback hợp lệ nếu effort của build composer chưa đáng cho tranche hiện tại.

## Ưu điểm

### Giảm context bootstrap

Nếu `SKILL.md` chỉ còn contract cốt lõi, agent sẽ nạp ít prose trùng lặp hơn trước khi bắt đầu công việc thật.

Current repo state: baseline hiện tại đã đủ lớn để lợi ích này là thực, ngay cả khi chưa recompute token cost chính xác.

### Single source of truth rõ hơn

Khi routing data nằm ở registry và deep detail nằm ở references:

- thay đổi intent/complexity/chain không cần vá nhiều bảng markdown
- drift giữa core và adapter giảm mạnh
- contract test có thể khóa canonical source thay vì khóa bản sao prose

### Scale tốt hơn khi Forge tiếp tục lớn lên

Thêm workflow hoặc operator action mới không nên tự động làm `SKILL.md` phình ra. Chỉ những thay đổi làm đổi bootstrap contract mới được quyền tăng kích thước `SKILL.md`.

### Adapter overlays sạch hơn

Nếu merge semantics được bổ sung đúng cách, overlay có thể tập trung vào host delta:

- Codex: operator surface, delegation, AGENTS boundary
- Antigravity: protocol bridge, artifact boundary, operator surface

Proposed direction: adapter file càng host-specific càng tốt; shared policy chỉ nên tồn tại một nơi.

## Nhược điểm

### Agent phải follow pointers thay vì thấy mọi thứ inline

Risk thật là agent có thể dựa vào memory thay vì mở registry/reference khi cần detail.

Mitigation đề xuất:

- giữ `Skill Composition Matrix` inline ở bản compact
- giữ rules và verification inline
- dùng `references/reference-map.md` như entrypoint rõ ràng thay vì ném nhiều pointer rời rạc

### Bootstrap latency tăng nhẹ

Flow đọc có thể thành:

`SKILL.md` -> `reference-map` hoặc `kernel-tooling` -> deep detail cần thiết

Đây là tradeoff chấp nhận được nếu bootstrap file ngắn hơn rõ rệt và pointer đủ kỷ luật.

### Behavioral drift nếu thin quá mức

Nếu cắt luôn Golden Rules, Iron Laws, hoặc Verification Strategy ra khỏi `SKILL.md`, agent rất dễ mất những guardrail mà nó phải giữ liên tục trong đầu.

Ranh giới cần giữ:

- rules, laws, verification, host delta: inline
- lookup data, inventories, long prose: delegate

### Test impact không phải là rewrite các heading assertions hiện có

Current repo state: current suite không khóa cứng việc `SKILL.md` phải có các heading như `Intent Detection` hoặc `Complexity Assessment`.

Actual work cần làm nếu triển khai thin-SKILL:

- thêm bootstrap-contract tests cho `SKILL.md`
- thêm anti-dup tests giữa core và overlays
- cân nhắc line-budget tests để chống file phình trở lại

Nói cách khác, cost test nằm ở việc thêm guardrail mới đúng bài toán, không phải chỉ sửa vài expectation cũ.

## Ranh giới quyết định

| Inline trong `SKILL.md` | Delegate sang registry/reference |
|-------------------------|----------------------------------|
| Golden Rules | Intent keyword table |
| Iron Laws per skill | Complexity threshold table |
| Verification Strategy | Error Translation catalog |
| Skill loading procedure | Bundle Layout tree |
| Skill Composition Matrix bản compact | Tooling inventory chi tiết |
| Independence Rule | Personalization detail dài |
| Host protocol/operator delta | Global Resilience prose |
| Reference-map pointer | Các lookup table khác |

Tooling pointer current nên đi về `references/kernel-tooling.md`, không mở thêm một current source cạnh tranh cho cùng surface.

## Các giải pháp thay thế đã cân nhắc

### Approach A: Trim duplicates only

Giữ structure hiện tại, chỉ xóa một phần section trùng registry.

Ưu điểm:

- risk thấp
- ít đụng build semantics

Nhược điểm:

- file vẫn dài
- duplication giữa core và adapter vẫn còn đáng kể
- không tạo được long-term guardrail chống phình

### Approach B: Core shrink trước, overlay chưa delta-only

Co `forge-core/SKILL.md` trước, còn adapter vẫn giữ nhiều shared prose hơn một thời gian.

Ưu điểm:

- có thể đi theo tranche
- không đòi merge semantics ngay lập tức

Nhược điểm:

- giảm duplication không triệt để
- adapter vẫn nặng
- dễ mắc kẹt ở trạng thái nửa vời

### Approach C: Thin-SKILL staged path

#### C1. Generated merged adapter artifact

Core giữ bootstrap contract ngắn.
Overlay chỉ giữ host delta.
Build sinh ra merged adapter `SKILL.md` từ core thin-SKILL + adapter delta.

Đây là end-state sạch nhất, nhưng cần thêm một cơ chế assemble rõ ràng. Có ít nhất ba cách khả thi:

- đánh dấu merge points trong core `SKILL.md`
- thêm một composer hẹp chỉ dành cho `SKILL.md` trong build
- thêm template engine tối giản cho adapter skill assembly

Ưu điểm:

- giải quyết đúng gốc duplication
- giữ adapter bootstrap đủ shared rules lẫn host delta
- scale tốt nhất về lâu dài

Nhược điểm:

- phải thay đổi build/generation contract
- cần chốt merge mechanism trước khi implement
- cần thêm test guardrail mới

Effort ước tính: `medium`.

#### C2. Compact overwrite fallback

Core vẫn được thin lại.
Adapter overlay vẫn overwrite `SKILL.md` như hiện tại, nhưng nội dung chỉ giữ:

- host delta
- compact shared rules thật sự cần visible trong adapter bundle

Ưu điểm:

- không cần thay đổi build pipeline hiện tại
- vẫn giảm mạnh kích thước và duplication so với state hiện tại
- phù hợp cho tranche muốn lấy maintenance win trước

Nhược điểm:

- vẫn còn duplication ở phần compact shared rules
- chưa đạt được single-source-of-truth sạch như C1
- có nguy cơ dừng luôn ở trạng thái "đỡ hơn nhưng chưa xong"

Effort ước tính: `low-medium`.

Đây là fallback hợp lệ nếu C1 quá nặng cho tranche hiện tại.

### Approach D: Pure pointer

`SKILL.md` gần như chỉ còn frontmatter + vài pointer.

Ưu điểm:

- nhỏ nhất

Nhược điểm:

- behavioral drift risk quá cao
- agent mất bootstrap contract
- verification/routing laws không còn đủ visible

Kết luận: quá cực đoan cho Forge hiện tại.

## Prerequisites để chuyển thành plan

Trước khi brainstorm này được nâng thành implementation plan, cần khóa 3 prerequisite:

1. **Canonical source boundaries**
   - cái gì ở registry
   - cái gì ở references
   - cái gì bắt buộc ở inline bootstrap

2. **Adapter assembly strategy**
   - nếu chọn C1: khóa merge mechanism cụ thể cho `SKILL.md`
   - nếu chọn C2: khóa chính xác phần compact shared rules nào vẫn được phép duplicate ở adapter
   - không để implementer tự quyết giữa merge-composer và compact-overwrite

3. **New test guardrails**
   - bootstrap-contract tests
   - anti-dup tests giữa core và overlays
   - line-budget tests nếu muốn khóa maintenance cost

## Kết luận

Bản revised này vẫn ủng hộ mạnh hướng `Thin-SKILL Contract-Only`.

Current repo state cho thấy vấn đề là có thật: `SKILL.md` đã đủ dài và đủ trùng để tạo maintenance cost rõ ràng. Tuy vậy, hướng `adapter delta-only` thuần túy không thể triển khai an toàn trên build semantics hiện tại.

Revised recommendation:

- co `SKILL.md` về bootstrap contract
- chuyển lookup data sang registry và deep prose sang references
- coi `generated merged SKILL artifact` là target state sạch hơn
- cho phép `compact overwrite fallback` nếu tranche hiện tại chưa đáng đầu tư build composer

Nói ngắn gọn: hướng đi đúng là thin-SKILL. Target state tốt nhất là `thin contract + generated merge + test guardrails`; còn path thực dụng hơn cho tranche gần là `thin contract + compact overwrite + test guardrails`.
