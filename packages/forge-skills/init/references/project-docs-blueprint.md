# Forge Bootstrap Docs Blueprint v2.4

> Đây là blueprint canonical cho bootstrap docs trong Forge.
> Blueprint này là reference của `forge-init`; output thật được render vào từng workspace.

## Mục tiêu

Blueprint này giúp `forge-init`:

- tạo bootstrap docs cho workspace mới;
- merge hoặc normalize docs đã có;
- giữ bootstrap docs ngắn, project-specific, và đủ cụ thể để AI làm đúng;
- tách rõ project docs khỏi execution memory của Forge.

Blueprint này không phải output cuối cho project và không được copy nguyên văn vào workspace.

## Vai trò trong Forge

### 1. Blueprint canonical sống trong Forge

- Blueprint này là reference canonical của Forge cho bootstrap docs.
- Vị trí mục tiêu trong skill pack là `forge-init/references/project-docs-blueprint.md`.
- `forge-init` đọc blueprint này trước khi tạo hoặc normalize docs cho workspace.

### 2. Workspace chỉ giữ artifact đã render

- Workspace nhận các file project-specific như `AGENTS.md`, `docs/PRODUCT.md`, `docs/STACK.md`.
- Workspace không giữ blueprint canonical như một file bắt buộc phải đọc ở mỗi session.

### 3. Forge global vẫn giữ process và state

Blueprint này không thay thế:

- global orchestrator;
- skill routing;
- verification invariants;
- `.forge-artifacts/workflow-state/*`;
- `.brain/session.json`, `.brain/handover.md`, `.brain/decisions.json`, `.brain/learnings.json`;
- session restore, save context, handover, hoặc selective closeout.

## Context Persistence Boundary

Forge tách project docs, execution state, và continuity sidecars:

- **Bootstrap docs**: `AGENTS.md`, `docs/PRODUCT.md`, `docs/STACK.md`, và optional project docs. Chúng mô tả project và local conventions; chúng không lưu task/session hiện tại.
- **Automatic execution state**: `.forge-artifacts/workflow-state/<project>/latest.json`, `packet-index.json`, và `events.jsonl`. `resume` có thể auto-seed workflow-state từ legacy artifacts hoặc latest `docs/plans` / `docs/specs` khi chưa có canonical workflow-state.
- **Explicit session continuity**: `forge-session-management save` ghi `.brain/session.json`; handover mới ghi `.brain/handover.md`.
- **Selective closeout**: closeout chỉ ghi `.brain/session.json`, `.brain/handover.md`, `.brain/decisions.json`, hoặc `.brain/learnings.json` khi có durable signal như pending step, verification note, risk, blocker, decision, hoặc learning.
- **Errors**: raw error output không phải durable `.brain` record. Chỉ lưu bài học, blocker, risk, decision, hoặc verification note sau khi error đã được diễn giải thành context hữu ích.

`forge-init` không tạo `.brain/session.json` mặc định. Nếu owner bật `--seed-continuity`, `forge-init` chỉ seed empty `.brain/decisions.json` và `.brain/learnings.json` để chuẩn bị continuity indexes.

## Ranh giới cần giữ

### Blueprint này sở hữu

- chuẩn bootstrap docs của workspace;
- cấu trúc docs nền tảng của project;
- rule generate, merge, normalize cho bootstrap docs;
- placeholder contract cho thông tin còn thiếu.

### Blueprint này không sở hữu

- workflow stage hiện tại;
- session memory;
- handover ngắn hạn;
- raw decision log của agent;
- raw error log của agent;
- verification contract toàn cục của Forge.

### Hệ quả thiết kế

- `STATUS.md` không phải file mặc định trong Forge workspaces.
- `DECISIONS.md` và `ERRORS.md` chỉ là curated project docs khi thật sự cần, không phải primary execution memory.
- `.brain/*` là continuity sidecar của Forge, không phải bootstrap docs output mặc định.

## Mô hình tài liệu của Forge

```text
forge bundle
└── forge-init/
    └── references/
        └── project-docs-blueprint.md

workspace/
├── AGENTS.md
├── docs/
│   ├── PRODUCT.md
│   ├── STACK.md
│   ├── ARCHITECTURE.md
│   ├── QUALITY.md
│   ├── SCHEMA.md
│   ├── OPERATIONS.md
│   └── templates/
│       └── FEATURE_TASK.md
├── .forge-artifacts/
│   └── workflow-state/
└── .brain/
```

`.forge-artifacts/` và `.brain/` là state/continuity layers. Chúng không thuộc default bootstrap docs.

## Nguyên tắc cốt lõi

1. **Bootstrap docs là project contract, không phải process engine.**
2. **Forge global owns process; workspace docs own local truth.**
3. **Không copy nguyên blueprint vào workspace.**
4. **Không dùng bootstrap docs để thay thế `.brain` hay workflow-state.**
5. **Không tạo `.brain/session.json` trong bootstrap flow.**
6. **Repo-specific content only**: mọi file render ra workspace phải nói về project cụ thể.
7. **Ngắn nhưng quyết định được hành vi**: chỉ giữ rule thật sự đổi được kết quả.
8. **Executable truth thắng docs cũ**: tests, build, schema, config và source code có ưu tiên cao hơn docs stale.
9. **Merge trước, tạo mới sau**: nếu repo đã có docs tương đương thì normalize hoặc reuse.
10. **Placeholder phải rõ ràng**: thiếu dữ liệu vẫn tạo skeleton usable ngay.
11. **Verification before claims** vẫn phản ánh trong docs local, nhưng contract toàn cục thuộc Forge.

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
- `.brain/session.json`

Ba docs `STATUS`, `DECISIONS`, và `ERRORS` chỉ nên xuất hiện nếu owner muốn curated docs dành cho người đọc. Chúng không thay `.brain` hoặc workflow-state.

## Bootstrap output phải trông như thế nào

### `AGENTS.md`

`AGENTS.md` trong workspace là local augmentation, không phải global orchestrator thứ hai.

Nó phải:

- nói project này là gì trong 1-2 câu;
- chỉ ra local source-of-truth order trong workspace;
- nói khi nào đọc `PRODUCT`, `STACK`, `ARCHITECTURE`, `QUALITY`, `SCHEMA`, `OPERATIONS`;
- nhắc rằng Forge global rules vẫn có hiệu lực;
- giữ mỏng, không duplicate session-management, routing, hay process rules của Forge.

Nó không được:

- định nghĩa lại workflow selection của Forge;
- tự tạo memory song song với `.brain`;
- copy lại global verification rules dài dòng;
- nhét stack detail vốn nên nằm trong `docs/STACK.md`.

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
- Do not write `.brain/session.json` from bootstrap docs; use Forge session-management save or closeout.
- Ask before changing schema, public API, CI, deploy, secrets, auth, payment, or destructive operations.
```

## Foundation docs

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

## Optional docs và rule tạo

### `docs/ARCHITECTURE.md`

Tạo khi project đã có từ 2 boundary chính trở lên, hoặc bootstrap cần cố định ownership và dependency direction sớm.

### `docs/QUALITY.md`

Tạo khi đã có hoặc gần có verification pattern lặp lại: test command, lint/typecheck, smoke check, release gate.

### `docs/SCHEMA.md`

Tạo khi project đã có contract đáng kể: API payload, event schema, file format, hoặc DB contract.

### `docs/OPERATIONS.md`

Tạo khi project có deploy, release, rollback, hoặc production concern thật.

### `docs/templates/FEATURE_TASK.md`

Tạo khi team sẽ giao việc cho AI thường xuyên và muốn chuẩn hóa input.

## Curated docs không phải mặc định

### `docs/DECISIONS.md`

Chỉ tạo khi project muốn một technical decision log curated cho người đọc hoặc cross-host AI đọc nhanh. Raw execution memory thuộc `.brain/decisions.json`.

### `docs/ERRORS.md`

Chỉ tạo khi có lỗi lặp lại hoặc fix non-obvious thật sự đáng giữ trong docs dự án. Không dùng file này như debug log.

### `docs/STATUS.md`

Không tạo mặc định. Nếu owner vẫn muốn file này, phải ghi rõ đây là curated project status, không phải primary session state của Forge.

## Placeholder contract

Khi thiếu dữ liệu, `forge-init` phải dùng placeholder rõ ràng:

- `[NEEDS INPUT: ...]`
- `[TO BE CONFIRMED: ...]`

Không dùng `TODO`, `TBD`, `fill later`, hoặc text mơ hồ.

## Contract của `forge-init`

Khi `forge-init` được gọi để bootstrap docs, nó phải:

1. Đọc blueprint canonical này trước.
2. Inspect workspace hiện tại trước khi tạo gì.
3. Phân loại workspace: `greenfield`, `existing-no-docs`, `existing-with-docs`, hoặc `normalize-existing-docs`.
4. Tìm file tương đương trước khi tạo mới.
5. Tạo bootstrap docs tối thiểu: `AGENTS.md`, `docs/PRODUCT.md`, `docs/STACK.md`.
6. Chỉ tạo docs optional khi có đủ tín hiệu hoặc user yêu cầu.
7. Không tạo mặc định `STATUS.md`, `DECISIONS.md`, `ERRORS.md`, hoặc `.brain/session.json`.
8. Không overwrite file hiện có trừ khi user yêu cầu rõ hoặc mode normalize đã được chọn.
9. Không copy nguyên blueprint vào workspace.
10. Báo kết quả rõ ràng: created, reused, normalized, missing inputs, và recommended next workflow.

### Default next workflow

- `greenfield` -> `brainstorm`
- `existing-*` -> `plan`

## Merge và normalize policy

Khi workspace đã có docs:

- ưu tiên giữ file đang có nếu nó đã gần đúng;
- normalize heading, structure, naming, source-of-truth wording khi cần;
- tránh tạo file trùng nghĩa chỉ vì khác tên.

## Điều tuyệt đối không làm

- Không biến bootstrap docs thành orchestrator cạnh tranh với Forge global.
- Không copy nguyên blueprint canonical sang workspace.
- Không dùng bootstrap docs để lưu session state.
- Không để `AGENTS.md` lặp lại session restore hoặc skill routing của Forge.
- Không tạo `.brain/session.json` mặc định.
- Không tạo `STATUS.md` mặc định như memory file.
- Không tạo hàng loạt docs optional khi chưa có dữ liệu.
- Không sửa code để khớp docs cũ nếu executable truth đang nói khác.

## Cách kiểm tra bootstrap đạt chuẩn

Mở một session sạch và hỏi:

1. Project này làm gì?
2. Nếu cần đổi behavior, phải đọc file nào trước?
3. Local source of truth ở workspace này là gì?
4. Docs nào là foundation docs, docs nào là optional?
5. Workspace này có dùng docs để thay execution memory của Forge không?
6. Bootstrap flow có tạo `.brain/session.json` không?

Nếu AI trả lời sai hoặc nhập nhằng các điểm trên, bootstrap docs chưa đạt chuẩn.

## Kết luận

Forge bootstrap docs chuẩn không phải wiki dài và không phải memory system.

Mô hình thống nhất:

- **Blueprint canonical**: nằm trong `forge-init/references/`.
- **Bootstrap behavior**: do `forge-init` sở hữu, chỉ tạo/normalize project docs.
- **Workspace docs**: là output project-specific.
- **Automatic execution state**: do workflow-state sở hữu.
- **Session continuity**: do `forge-session-management` save, handover, và closeout sở hữu.
