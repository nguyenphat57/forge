# Forge Bootstrap Docs Blueprint v2.3

> Đây là blueprint canonical cho bootstrap docs trong Forge.
> Blueprint này được thiết kế để sống như một reference của `forge-init`, còn bootstrap docs thật được render vào workspace của từng project.

---

## Mục tiêu

Blueprint này tồn tại để `forge-init` có một chuẩn ổn định khi:

- tạo bootstrap docs cho workspace mới
- merge hoặc normalize workspace đã có docs
- giữ bootstrap docs ngắn, đọc được, và đủ cụ thể để AI làm đúng
- tách rõ docs dự án khỏi execution memory của Forge

Blueprint này không phải là output cuối cho project, và không được copy nguyên văn vào workspace.

---

## Vai trò trong Forge

### 1. Blueprint canonical sống trong Forge

- Blueprint này là reference canonical của Forge cho bootstrap docs.
- Vị trí mục tiêu khi tích hợp vào skill pack là `forge-init/references/`.
- `forge-init` phải đọc blueprint này trước khi tạo hoặc normalize docs cho workspace.

### 2. Workspace chỉ giữ artifact đã render

- Workspace nhận các file project-specific như `AGENTS.md`, `docs/PRODUCT.md`, `docs/STACK.md`.
- Workspace không giữ lại blueprint canonical như một file bắt buộc để AI tự đọc ở mỗi session.

### 3. Forge global vẫn giữ process và state

Blueprint này không thay thế các phần sau của Forge:

- global orchestrator
- skill routing
- verification invariants
- `.brain/*`
- `.forge-artifacts/workflow-state/*`
- session restore, save, handover

---

## Ranh giới cần giữ

### Blueprint này sở hữu

- chuẩn bootstrap docs của workspace
- cấu trúc docs nền tảng của project
- rule generate, merge, normalize cho bootstrap docs
- placeholder contract cho thông tin còn thiếu

### Blueprint này không sở hữu

- workflow stage hiện tại
- session memory
- handover ngắn hạn
- decision log thô của agent
- error log thô của agent
- verification contract toàn cục của Forge

### Hệ quả thiết kế

- `STATUS.md` không phải file mặc định trong Forge workspaces.
- `DECISIONS.md` và `ERRORS.md` chỉ là curated project docs khi thật sự cần, không phải primary execution memory.
- `.brain/session.json`, `.brain/handover.md`, `.brain/decisions.json`, `.brain/learnings.json` vẫn là memory/state của Forge.

---

## Mô hình tài liệu của Forge

```text
forge bundle
└── forge-init/
    └── references/
        └── project-docs-blueprint.md   ← blueprint canonical

workspace/
├── AGENTS.md                           ← local augmentation, project-specific
├── CLAUDE.md                           ← optional thin adapter
├── GEMINI.md                           ← optional thin adapter
├── .github/
│   └── copilot-instructions.md         ← optional thin adapter
└── docs/
    ├── PRODUCT.md
    ├── STACK.md
    ├── ARCHITECTURE.md                 ← optional
    ├── QUALITY.md                      ← optional
    ├── SCHEMA.md                       ← optional
    ├── OPERATIONS.md                   ← optional
    ├── DECISIONS.md                    ← optional curated doc
    ├── ERRORS.md                       ← optional curated doc
    └── templates/
        └── FEATURE_TASK.md             ← optional
```

Forge state nằm ngoài bootstrap docs:

```text
workspace/
├── .brain/
└── .forge-artifacts/
```

---

## Nguyên tắc cốt lõi

1. **Bootstrap docs là project contract, không phải process engine.**
2. **Forge global owns process; workspace docs own local truth.**
3. **Không copy nguyên blueprint vào workspace.**
4. **Không dùng bootstrap docs để thay thế `.brain` hay `workflow-state`.**
5. **Repo-specific content only**: mọi file render ra workspace phải nói về project cụ thể.
6. **Ngắn nhưng quyết định được hành vi**: chỉ giữ rule thật sự đổi được kết quả.
7. **Executable truth thắng docs cũ**: tests, build, schema, config và source code có ưu tiên cao hơn docs stale.
8. **Merge trước, tạo mới sau**: nếu repo đã có docs tương đương thì normalize hoặc reuse.
9. **Placeholder phải rõ ràng**: thiếu dữ kiện vẫn tạo skeleton usable ngay.
10. **Verification before claims** vẫn phải phản ánh trong docs local, nhưng contract toàn cục vẫn thuộc Forge.

---

## Bộ bootstrap docs mặc định

### Luôn tạo hoặc normalize

- `AGENTS.md`
- `docs/PRODUCT.md`
- `docs/STACK.md`

### Chỉ tạo khi có đủ tín hiệu hoặc project cần ngay

- `docs/ARCHITECTURE.md`
- `docs/QUALITY.md`
- `docs/SCHEMA.md`
- `docs/OPERATIONS.md`
- `docs/templates/FEATURE_TASK.md`

Root `CHANGELOG.md` creation belongs to `forge-bump-release`, not `forge-init`.

### Không tạo mặc định trong Forge workspace

- `docs/STATUS.md`
- `docs/DECISIONS.md`
- `docs/ERRORS.md`

Ba file này chỉ nên xuất hiện nếu owner muốn có curated docs dành cho người đọc, không phải để thay `.brain`.

---

## Bootstrap output phải trông như thế nào

### `AGENTS.md`

`AGENTS.md` trong workspace là local augmentation, không phải một global orchestrator thứ hai.

Nó phải:

- nói project này là gì trong 1-2 câu
- chỉ ra local source-of-truth order trong phạm vi workspace
- nói khi nào đọc `PRODUCT`, `STACK`, `ARCHITECTURE`, `QUALITY`, `SCHEMA`, `OPERATIONS`
- nhắc rằng Forge global rules vẫn có hiệu lực
- giữ mỏng, không duplicate session-management, routing, hay process rules của Forge

Nó không được:

- định nghĩa lại workflow selection của Forge
- tự tạo một hệ memory song song với `.brain`
- copy lại global verification rules theo kiểu dài dòng
- nhét quá nhiều stack detail vốn nên nằm trong `docs/STACK.md`

### Mẫu `AGENTS.md`

```markdown
# [Tên Project]

## Summary
[1-2 câu mô tả project, users chính, outcome chính]

## Relationship To Forge
- Keep Forge global orchestration, verification, and session rules.
- This file is workspace-local augmentation only.

## Local Source Of Truth
1. Current user request / ticket / task packet
2. This file (`AGENTS.md`)
3. Executable truth: tests, typecheck, build config, schema, migrations, generators
4. Current repo source code
5. `docs/PRODUCT.md`
6. `docs/STACK.md`
7. `docs/ARCHITECTURE.md` when present
8. `docs/QUALITY.md` when present
9. `docs/SCHEMA.md` when present
10. `docs/OPERATIONS.md` when present

## Read Triggers
- Read `docs/PRODUCT.md` before scoping, planning, or changing user-facing behavior.
- Read `docs/STACK.md` before changing commands, tooling, runtimes, dependencies, or codegen.
- Read `docs/ARCHITECTURE.md` before changing boundaries, ownership, or cross-module flow.
- Read `docs/QUALITY.md` before choosing proof depth or adding/changing verification.
- Read `docs/SCHEMA.md` before changing payloads, APIs, schemas, or file formats.
- Read `docs/OPERATIONS.md` before touching release, deploy, rollback, production config, or observability.

## Local Rules
- Prefer existing repo patterns before introducing new ones.
- Surface doc/code conflicts explicitly instead of silently following stale docs.
- Ask before changing schema, public API, CI, deploy, secrets, auth, payment, or destructive operations.
```

### `docs/PRODUCT.md`

File này trả lời: project giải quyết vấn đề gì, cho ai, scope nào, không làm gì.

Mẫu tối thiểu:

```markdown
# Product Brief

## Problem
[Project đang giải quyết vấn đề gì?]

## Users
[Ai dùng, trong ngữ cảnh nào?]

## Goals
- [...]

## Non-goals
- [...]

## Main flows
1. [...]

## Acceptance criteria
- [...]
```

### `docs/STACK.md`

File này trả lời: dùng gì, chạy lệnh nào, convention nào, generated artifacts nào, dependency policy nào.

Mẫu tối thiểu:

```markdown
# Stack And Conventions

## Runtime
- [...]

## Core libraries and frameworks
| Name | Version | Purpose |
|------|---------|---------|
| [...] | [...] | [...] |

## Commands
- Install: `...`
- Dev: `...`
- Test: `...`
- Lint: `...`
- Typecheck / Build: `...`

## Dependency policy
- Prefer existing stack first.
- Ask before adding new dependency or major upgrade.

## Generated artifacts
- [...]

## Sensitive config
- Secrets must use the project-approved config path, never source or logs.
```

---

## Các docs optional và rule tạo

### `docs/ARCHITECTURE.md`

Tạo khi project đã có từ 2 boundary chính trở lên, hoặc bootstrap cần cố định ownership và dependency direction sớm.

### `docs/QUALITY.md`

Tạo khi đã có hoặc gần có verification pattern lặp lại:

- test command
- lint/typecheck
- smoke check
- release gate

### `docs/SCHEMA.md`

Tạo khi project đã có contract đáng kể:

- API payload
- event schema
- file format
- DB contract

### `docs/OPERATIONS.md`

Tạo khi project có deploy/release/production concern thật.

### `docs/templates/FEATURE_TASK.md`

Tạo khi team sẽ giao việc cho AI thường xuyên và muốn chuẩn hóa input.

---

## Curated docs không phải mặc định

### `docs/DECISIONS.md`

Chỉ tạo khi project muốn một bản technical decision log dành cho con người hoặc cross-host AI đọc nhanh.

Không dùng file này như raw execution memory. Raw memory thuộc `.brain/decisions.json`.

### `docs/ERRORS.md`

Chỉ tạo khi có lỗi lặp lại hoặc fix non-obvious thật sự đáng giữ trong docs dự án.

Không dùng file này như debug log. Debug memory thô không thuộc bootstrap docs.

### `docs/STATUS.md`

Không tạo mặc định trong Forge workspaces.

Nếu owner vẫn muốn file này, phải ghi rõ đây là curated project status cho người đọc, không phải primary session state của Forge.

---

## Placeholder contract

Khi thiếu dữ kiện, `forge-init` phải dùng placeholder rõ ràng:

- `[NEEDS INPUT: ...]`
- `[TO BE CONFIRMED: ...]`

Placeholder phải:

- ngắn
- action-oriented
- chỉ ra đúng thông tin còn thiếu
- không để `TODO`, `TBD`, hoặc text mơ hồ

Ví dụ tốt:

- `[NEEDS INPUT: primary user persona for the first release]`
- `[TO BE CONFIRMED: production deployment target and rollback owner]`

Ví dụ không dùng:

- `TODO`
- `fill later`
- `add more details`

---

## Contract của `forge-init`

Khi `forge-init` được gọi để bootstrap docs, nó phải:

1. Đọc blueprint canonical này trước.
2. Inspect workspace hiện tại trước khi tạo gì.
3. Phân loại workspace:
   - `greenfield`
   - `existing-no-docs`
   - `existing-with-docs`
   - `normalize-existing-docs`
4. Tìm file tương đương trước khi tạo mới.
5. Tạo bootstrap docs tối thiểu:
   - `AGENTS.md`
   - `docs/PRODUCT.md`
   - `docs/STACK.md`
6. Chỉ tạo docs optional khi có đủ tín hiệu hoặc user yêu cầu.
7. Không tạo mặc định `STATUS.md`, `DECISIONS.md`, `ERRORS.md`.
8. Không overwrite file hiện có trừ khi user yêu cầu rõ hoặc mode normalize đã được chọn.
9. Không copy nguyên blueprint vào workspace.
10. Báo kết quả rõ ràng:
   - file nào tạo
   - file nào reuse
   - file nào normalize
   - file nào chưa tạo vì thiếu dữ kiện
   - placeholder nào cần owner điền
   - next workflow là `brainstorm` hay `plan`

### Default next workflow

- `greenfield` -> `brainstorm`
- `existing-*` -> `plan`

---

## Merge và normalize policy

Khi workspace đã có docs:

- ưu tiên giữ file đang có nếu nó đã gần đúng
- normalize heading, structure, naming, source-of-truth wording khi cần
- tránh tạo file trùng nghĩa chỉ vì khác tên

Ví dụ:

- repo đã có `docs/product.md` với nội dung đúng -> normalize sang `docs/PRODUCT.md` hoặc reuse theo repo convention, không nhân đôi
- repo đã có `README` chứa đủ stack commands nhưng chưa có `docs/STACK.md` -> có thể trích xuất thành `docs/STACK.md` nếu user muốn chuẩn hóa

---

## Điều tuyệt đối không làm

- Không biến bootstrap docs thành một orchestrator cạnh tranh với Forge global
- Không copy nguyên văn blueprint canonical sang workspace
- Không dùng bootstrap docs để lưu session state
- Không để `AGENTS.md` lặp lại session restore hoặc skill routing của Forge
- Không tạo `STATUS.md` mặc định như một memory file
- Không tạo hàng loạt docs optional khi chưa có dữ kiện
- Không sửa code để khớp docs cũ nếu executable truth đang nói khác

---

## Cách kiểm tra một bootstrap có đạt chuẩn không

Mở một session sạch và hỏi:

1. Project này làm gì?
2. Nếu cần đổi behavior, phải đọc file nào trước?
3. Local source of truth ở workspace này là gì?
4. Docs nào là foundation docs, docs nào là optional?
5. Workspace này có đang dùng docs để thay execution memory của Forge không?

Nếu AI trả lời sai hoặc nhập nhằng các điểm trên, bootstrap docs chưa đạt chuẩn.

---

## Kết luận

Forge bootstrap docs chuẩn không phải là một bộ wiki dài, cũng không phải một hệ memory cạnh tranh với Forge state.

Nó là một contract nhỏ, project-specific, được sinh ra từ một blueprint canonical của `forge-init`, với mục tiêu:

- giúp AI hiểu project nhanh
- giữ local truth rõ ràng
- không chồng chéo với `.brain` hay `workflow-state`
- làm bước tiếp theo trong Forge trở nên rõ ràng: `brainstorm` hoặc `plan`

Tóm tắt mô hình:

- **Blueprint canonical**: nằm trong `forge-init/references/`
- **Bootstrap behavior**: do `forge-init` sở hữu
- **Workspace docs**: là output project-specific
- **Execution memory**: vẫn do Forge state sở hữu
