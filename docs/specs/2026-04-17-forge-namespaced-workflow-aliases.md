# Spec: Forge Namespaced Workflow Aliases

Status: implemented

## Goal

Chuẩn hóa surface slash command dạng `/forge:<workflow>` để Forge có thể gọi đúng workflow theo tên thật của workflow, thay vì phụ thuộc vào alias ngắn lịch sử như `/code`, `/design`, hoặc `/audit`.

## Scope

Trong scope:
- Expose alias namespaced cho toàn bộ workflow names trên core design/execution surface.
- Expose alias namespaced cho host-specific execution workflows mà host đó public, như `dispatch-subagents` trên Codex.
- Giữ alias ngắn hiện có như compatibility surface.
- Khi prompt bắt đầu bằng `/forge:<workflow>`, route phải coi đó là exact workflow invocation.
- Generated host artifacts phải render cùng một contract namespaced thay vì hand-maintain bảng alias.

Ngoài scope:
- Không đổi stage order hiện có.
- Không bỏ alias ngắn cũ.
- Không thêm workflow mới.
- Không đổi semantics của natural-language routing.

## Canonical Behavior

### 1. Exact namespaced alias

Alias `/forge:<workflow>` luôn dùng đúng workflow name đã khai báo trong workflow metadata.

Ví dụ:
- `/forge:brainstorm`
- `/forge:plan`
- `/forge:architect`
- `/forge:spec-review`
- `/forge:visualize`
- `/forge:build`
- `/forge:debug`
- `/forge:test`
- `/forge:review`
- `/forge:refactor`
- `/forge:secure`
- `/forge:quality-gate`
- `/forge:deploy`
- `/forge:session`
- `/forge:dispatch-subagents` trên Codex

### 2. Compatibility aliases stay intact

Alias ngắn cũ vẫn giữ nguyên để không break existing usage.

Ví dụ:
- `/design` vẫn map sang `architect`
- `/code` vẫn map sang `build`
- `/audit` vẫn map sang `secure`

### 3. Exact workflow invocation semantics

`/forge:<workflow>` là exact workflow invocation, không phải intent shortcut.

Hệ quả:
- `/forge:build` chọn thẳng workflow `build`, không tự chèn lại `plan`
- `/forge:quality-gate` chọn thẳng workflow `quality-gate`
- `/forge:session` chọn thẳng workflow `session`

Ngược lại, alias ngắn cũ vẫn có thể giữ semantics convenience hiện tại nếu đã tồn tại ở host/routing layer.

## Source Of Truth

Workflow namespaced aliases phải được suy ra từ workflow metadata, không được copy tay ở nhiều chỗ.

Source-of-truth tối thiểu:
- workflow `name`
- workflow path
- legacy shortcut nếu có

Generated host docs và route preview phải cùng dùng chung source này.

## Host Surface Rules

### Codex

- Render namespaced aliases cho toàn bộ core design/execution workflows.
- Render thêm namespaced alias cho `dispatch-subagents`.
- Giữ operator aliases riêng; không trộn chúng vào workflow namespace nếu không có exact workflow metadata tương ứng trên execution/design surface.

### Antigravity

- Render namespaced aliases cho toàn bộ core design/execution workflows.
- Không invent host-only workflow aliases ngoài inventory thực tế.

## Verification

Verification cho tranche này phải chứng minh được 2 điều:

1. Host artifact generation:
- Generated AGENTS/GEMINI globals hiển thị namespaced aliases đúng với workflow names.
- Legacy aliases vẫn còn.

2. Routing:
- Route preview nhận diện `/forge:<workflow>` như explicit workflow invocation.
- `forge_skills` phản ánh workflow được chỉ định trực tiếp.
- Existing natural-language routing và compatibility aliases không regress.

## Reopen Conditions

Chỉ reopen spec nếu:
- Forge quyết định namespaced alias phải bao gồm operator workflows.
- Workflow metadata không đủ để render alias surface deterministically.
- Exact workflow invocation semantics xung đột với contract hiện tại của host.
