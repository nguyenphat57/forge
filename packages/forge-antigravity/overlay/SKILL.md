---
name: forge-antigravity
description: "Forge Antigravity - skill-oriented orchestrator optimized for Antigravity workspaces. Use when a request needs intent routing, complexity assessment, skill composition, Antigravity-friendly session handling, shared delivery guardrails, and optional companion runtime/language skill integration across planning, building, debugging, reviewing, designing, testing, deploying, or session restore/save work."
---

# Forge Antigravity - Core Orchestrator

> Forge = delivery discipline + skill composition + evidence before claims.
> Forge phải đủ mạnh và đủ kỷ luật ngay cả khi repo chưa có companion skill hay local skill nào.
> Forge linh hoạt ở những task nhỏ và kỷ luật ở những task vừa và lớn.

---

## Bundle Layout

Cây thư mục bên dưới phản ánh bundle Antigravity sau khi overlay adapter này lên trên `forge-core`.
Các file kế thừa từ core và các file do adapter thêm vào cùng xuất hiện trong một runtime layout.

- `SKILL.md`: entrypoint để route intent, ghép skill, và giữ delivery guardrails
- `workflows/design/`: planning, architecture, spec-review, visualize
- `workflows/execution/`: build, debug, test, review, refactor, secure, deploy, session
- `workflows/operator/`: help, next, run, bump, rollback, và các wrapper Antigravity như customize/init/recap/save-brain/handover
- `domains/`: core domain guidance cho frontend và backend
- `data/`: machine-readable registry cho intent, matrix, verification profiles, quality profiles, execution pipelines, và lane model policy
- `scripts/`: deterministic tooling cho route preview, scoped continuity capture, và các kiểm tra tùy chọn cho workspace có local layer
- `tests/`: regression tests cho deterministic scripts và router/tooling contracts
- `references/`: smoke tests, companion contract, và tài liệu tham chiếu chỉ đọc khi cần
- `agents/openai.yaml`: metadata UI cho host hỗ trợ skill list/chips

```text
forge-antigravity/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── data/
│   ├── orchestrator-registry.json
│   ├── preferences-compat.json
│   └── preferences-schema.json
├── domains/
│   ├── backend.md
│   └── frontend.md
├── references/
│   ├── antigravity-operator-surface.md
│   ├── backend-briefs.md
│   ├── bump-release.md
│   ├── canary-rollout.md
│   ├── companion-routing-smoke-tests.md
│   ├── companion-skill-contract.md
│   ├── error-translation.md
│   ├── execution-delivery.md
│   ├── failure-recovery-playbooks.md
│   ├── frontend-stack-profiles.md
│   ├── help-next.md
│   ├── personalization.md
│   ├── reference-map.md
│   ├── rollback-guidance.md
│   ├── run-guidance.md
│   ├── smoke-test-checklist.md
│   ├── smoke-tests.md
│   ├── tooling.md
│   ├── ui-briefs.md
│   ├── ui-escalation.md
│   ├── ui-good-bad-examples.md
│   ├── ui-heuristics.md
│   ├── ui-progress.md
│   ├── ui-quality-checklist.md
│   └── workspace-init.md
├── scripts/
│   ├── capture_continuity.py
│   ├── check_backend_brief.py
│   ├── check_ui_brief.py
│   ├── check_workspace_router.py
│   ├── common.py
│   ├── evaluate_canary_readiness.py
│   ├── generate_backend_brief.py
│   ├── generate_ui_brief.py
│   ├── initialize_workspace.py
│   ├── prepare_bump.py
│   ├── record_canary_result.py
│   ├── resolve_help_next.py
│   ├── resolve_preferences.py
│   ├── resolve_rollback.py
│   ├── route_preview.py
│   ├── run_smoke_matrix.py
│   ├── run_with_guidance.py
│   ├── run_workspace_canary.py
│   ├── track_chain_status.py
│   ├── track_execution_progress.py
│   ├── track_ui_progress.py
│   ├── translate_error.py
│   ├── verify_bundle.py
│   └── write_preferences.py
├── tests/
│   ├── fixtures/
│   ├── support.py
│   ├── test_bump_workflow.py
│   ├── test_canary_rollout.py
│   ├── test_check_workspace_router.py
│   ├── test_contracts.py
│   ├── test_error_translation.py
│   ├── test_help_next.py
│   ├── test_initialize_workspace.py
│   ├── test_preferences.py
│   ├── test_rollback_guidance.py
│   ├── test_router_matrix.py
│   ├── test_route_matrix.py
│   ├── test_route_preview.py
│   ├── test_run_workflow.py
│   ├── test_tool_roundtrip.py
│   ├── test_workspace_canary.py
│   └── test_write_preferences.py
└── workflows/
    ├── design/
    │   ├── architect.md
    │   ├── brainstorm.md
    │   ├── plan.md
    │   ├── spec-review.md
    │   └── visualize.md
    ├── execution/
        ├── build.md
        ├── debug.md
        ├── deploy.md
        ├── quality-gate.md
        ├── refactor.md
        ├── review.md
        ├── secure.md
        ├── session.md
        └── test.md
    └── operator/
        ├── bump.md
        ├── customize.md
        ├── handover.md
        ├── help.md
        ├── init.md
        ├── next.md
        ├── recap.md
        ├── rollback.md
        ├── run.md
        └── save-brain.md
```

## Host Boundary

- Rule của host Antigravity sống ở scope cao hơn folder này.
- Root `GEMINI.md` ở scope Antigravity, nếu host đang dùng nó, là **host rule file** chứ không phải một phần của skill bundle.
- `AGENTS.md` ở root workspace là **router/instruction file** của workspace, không phải `SKILL.md`.
- `forge-antigravity` có thể đọc host/workspace rules để route tốt hơn, nhưng không phụ thuộc vào một file local `GEMINI.md` nằm trong chính folder skill này.

## Independence Rule

- Forge là **global-first orchestrator**.
- Repo mới, repo nhỏ, hoặc repo chưa có local skills vẫn phải dùng Forge bình thường bằng chính workflows/domain skills của bundle này.
- Companion skills và workspace routers là **optional augmentation**, không phải dependency mặc định.
- Nếu không có companion/local skill rõ ràng, Forge không được chần chừ hay chờ “bộ skill đầy đủ” rồi mới làm việc.

---

## Executable Tooling

- Canonical machine-readable source: `data/orchestrator-registry.json`
- Preferences resolver: `scripts/resolve_preferences.py` (adapter-global Forge preferences -> canonical response-style contract, with optional legacy workspace fallback)
- Preferences writer: `scripts/write_preferences.py` (canonical schema persistence for `/customize`)
- Workspace init skeleton: `scripts/initialize_workspace.py` (repo-neutral bootstrap for `/init`)
- Help/next navigator: `scripts/resolve_help_next.py` (repo state -> current focus, suggested workflow, next action)
- Run guidance resolver: `scripts/run_with_guidance.py` (execute command -> classify signal -> route to test/debug/deploy)
- Error translator: `scripts/translate_error.py` (raw stderr/error text -> sanitized human summary + suggested action)
- Bump preparation: `scripts/prepare_bump.py` (explicit hoặc inferred semver bump -> update VERSION/CHANGELOG checklist)
- Rollback planner: `scripts/resolve_rollback.py` (scope/risk -> safest recovery strategy + verification)
- Deterministic route preview: `scripts/route_preview.py` (intent + chain + execution pipeline + lane model tiers)
- Workspace router drift check: `scripts/check_workspace_router.py` (chỉ dùng khi workspace thật sự có local routing layer)
- Scoped continuity capture for durable decisions/learnings: `scripts/capture_continuity.py`
- Backend brief generator for medium/large backend work: `scripts/generate_backend_brief.py`
- Backend brief checker for persisted backend artifacts: `scripts/check_backend_brief.py`
- Chain status tracker for long-running multi-skill flows: `scripts/track_chain_status.py` (stages + lanes + model tiers + review loop state)
- Execution progress tracker for long-running build work: `scripts/track_execution_progress.py` (checkpoint + lane + proof-before-progress)
- UI brief generator for frontend/visualize work: `scripts/generate_ui_brief.py`
- UI brief checker for persisted frontend/visualize artifacts: `scripts/check_ui_brief.py`
- UI progress tracker for long-running frontend/visualize tasks: `scripts/track_ui_progress.py`
- Automated smoke matrix runner for route/router cases: `scripts/run_smoke_matrix.py`
- Canonical release/CI verification entrypoint: `scripts/verify_bundle.py`
- Automated workspace canary runner for real repo rollout: `scripts/run_workspace_canary.py`
- Canary result recorder for real workspace rollout: `scripts/record_canary_result.py`
- Canary readiness evaluator for rollout verdicts: `scripts/evaluate_canary_readiness.py`
- Persisted artifacts mặc định:
  - `.forge-artifacts/route-previews/`
  - `.forge-artifacts/router-checks/`
  - `.forge-artifacts/backend-briefs/`
  - `.forge-artifacts/chain-status/`
  - `.forge-artifacts/execution-progress/`
  - `.forge-artifacts/ui-briefs/`
  - `~/.gemini/antigravity/forge-antigravity/state/preferences.json`
  - `~/.gemini/antigravity/forge-antigravity/state/extra_preferences.json`
  - `.brain/decisions.json`
  - `.brain/learnings.json`

Khi cần command examples hoặc artifact behavior chi tiết, đọc `references/tooling.md`.

---

## Response Personalization

- Forge resolve preferences qua core engine `scripts/resolve_preferences.py` từ Antigravity-global split state: canonical fields ở `state/preferences.json`, adapter extras ở `state/extra_preferences.json`, và chỉ fallback sang `.brain/preferences.json` cho workspace legacy.
- Schema canonical gồm `technical_level`, `detail_level`, `autonomy_level`, `pace`, `feedback_style`, và `personality`.
- Khi file state đang dùng payload native cũ của Antigravity, adapter này chỉ map payload đó về canonical schema để đọc hoặc migrate; steady-state write path vẫn là split-file canonical + extras của core.
- `forge-antigravity` ship compat defaults để clean install mặc định resolve `language=vi` và `orthography=vietnamese_diacritics` cho đến khi state hoặc workspace override chúng.
- `forge-antigravity` có thể thêm wrapper như `/customize`, nhưng schema và response-style semantics vẫn phải đọc từ core.
- Durable preference updates, bao gồm `language` và `orthography`, phải đi qua `scripts/write_preferences.py`; workspace `.brain/preferences.json` chỉ là override theo repo hoặc legacy fallback.
- Host UX có thể dày hơn Codex, nhưng không được fork key names hay validation rules.

---

## Operator Guidance

- `forge-antigravity` có thể expose rõ `/help` và `/next`, nhưng guidance vẫn phải resolve từ core navigator `scripts/resolve_help_next.py`.
- Repo-first vẫn là hard rule: `git status`, plans/specs, rồi mới đến `.brain`.
- Wrapper UX có thể operator-friendly hơn, nhưng không được biến guidance thành recap theater.
- `forge-antigravity` có thể expose rõ `/run`, nhưng kết quả vẫn phải resolve từ core `scripts/run_with_guidance.py`.
- Error translation vẫn đọc từ core helper `scripts/translate_error.py`; adapter này chỉ đổi presentation, không đổi pattern database.
- `/bump` và `/rollback` có thể được expose rõ ở Antigravity, nhưng vẫn phải giữ user-requested/inference-justified và risk-first contract của core.
- `/init` có thể dày hơn về onboarding, nhưng workspace skeleton reusable vẫn phải đi qua `scripts/initialize_workspace.py`.
- Session ergonomics wrappers như `/recap`, `/save-brain`, và `/handover` chỉ là bề mặt thuận tay trên `workflows/execution/session.md`.
- Wrapper này được dày hơn về UX, nhưng không được đổi `state`, `command_kind`, hay `suggested_workflow` của core.

---

## Antigravity Operator Surface

Primary wrappers:

| Surface | Wrapper | Core contract |
|---------|---------|---------------|
| `/help` | `workflows/operator/help.md` | `scripts/resolve_help_next.py --mode help` |
| `/next` | `workflows/operator/next.md` | `scripts/resolve_help_next.py --mode next` |
| `/run` | `workflows/operator/run.md` | `scripts/run_with_guidance.py` |
| `/bump` | `workflows/operator/bump.md` | `scripts/prepare_bump.py` |
| `/rollback` | `workflows/operator/rollback.md` | `scripts/resolve_rollback.py` |
| `/customize` | `workflows/operator/customize.md` | `scripts/resolve_preferences.py` + `scripts/write_preferences.py` |
| `/init` | `workflows/operator/init.md` | `scripts/initialize_workspace.py` |

Session wrappers:

| Alias | Wrapper | Core contract |
|-------|---------|---------------|
| `/recap` | `workflows/operator/recap.md` | `workflows/execution/session.md` restore mode |
| `/save-brain` | `workflows/operator/save-brain.md` | `workflows/execution/session.md` save mode |
| `/handover` | `workflows/operator/handover.md` | `workflows/execution/session.md` handover mode |

Compatibility rule:

- Alias chỉ được giảm friction migration, không tạo intent mới.
- Wrapper docs có thể operator-friendly hơn, nhưng deterministic semantics vẫn đọc từ core.
- Chi tiet mapping: `references/antigravity-operator-surface.md`.

---

## Intent Detection

Khi nhận prompt từ user, phân loại intent:

| Intent | Trigger keywords | Ví dụ |
|--------|------------------|-------|
| **BUILD** | thêm, tạo, implement, feature, code | "Thêm tính năng thanh toán" |
| **DEBUG** | lỗi, bug, fix, sửa, error, crash | "Fix lỗi không đăng nhập được" |
| **OPTIMIZE** | refactor, tối ưu, clean, dọn | "Refactor file quá dài" |
| **DEPLOY** | deploy, release, production, rollout | "Deploy lên Vercel" |
| **REVIEW** | review, đánh giá, kiểm tra, audit | "Review code trước khi merge" |
| **VISUALIZE** | ui, ux, mockup, wireframe, screen, layout | "Phác thảo màn hình checkout" |
| **SESSION** | recap, continue, resume, save, context | "Tiếp tục việc đang dở" |

**Khi user dùng `/shortcut`:** Map theo shortcut registry của host Antigravity, không phụ thuộc vào file local trong folder skill này.
Canonical source cho intent keywords và chains: `data/orchestrator-registry.json`.

Signals như `brainstorm`, `ý tưởng`, `nên chọn hướng nào`, `options`, `approach`, `tradeoff` không tạo intent mới; chúng bật **brainstorm gate** trước `plan` khi task đủ mơ hồ/phức tạp.

---

## Complexity Assessment

| Level | Tiêu chí | Ví dụ |
|-------|----------|-------|
| **small** | <=2 files, blast radius nhỏ, yêu cầu rõ | Fix typo, sửa CSS, đổi 1 field |
| **medium** | 3-10 files, có thay đổi hành vi hoặc cần assumption | Thêm filter, CRUD endpoint |
| **large** | >10 files hoặc feature/module mới, data flow rộng | Payment, auth flow, new module |

Nghi ngờ small hay medium -> mặc định **medium**.
Canonical source cho hints và thresholds: `data/orchestrator-registry.json`.

---

## Skill Composition Matrix

Intent + Complexity -> skills can load:

| Intent | small | medium | large |
|--------|-------|--------|-------|
| **BUILD** | `build` | `plan` -> `build` -> `test` -> `quality-gate` | `plan` -> `architect` -> `spec-review` -> `build` -> `test` -> `quality-gate` |
| **DEBUG** | `debug` | `debug` -> `test` | `debug` -> `plan` -> `build` -> `test` |
| **OPTIMIZE** | `refactor` | `refactor` -> `test` | `review` -> `refactor` -> `test` |
| **DEPLOY** | `deploy` | `secure` -> `quality-gate` -> `deploy` | `secure` -> `test` -> `quality-gate` -> `deploy` |
| **REVIEW** | `review` | `review` -> `secure` | `review` -> `secure` |
| **VISUALIZE** | `visualize` | `plan` -> `visualize` | `plan` -> `architect` -> `visualize` |
| **SESSION** | `session` | `session` | `session` |

**Ambiguity gate:** với `BUILD` hoặc `VISUALIZE` ở mức medium/large, nếu prompt còn mơ hồ hoặc đang cân giữa nhiều hướng giải, chèn `brainstorm` trước `plan`. `Brainstorm` không chỉ liệt kê options; nó phải khóa một hướng khuyến nghị đủ mạnh để `plan` kế thừa, hoặc ghi đúng một câu hỏi quyết định còn thiếu.
**Spec-review gate:** với `BUILD large`, hoặc `BUILD medium` chạm contract/schema/migration/auth/payment/public interface/high-risk boundary, chèn `spec-review` trước `build`.
**Execution pipeline gate:** với `BUILD/DEBUG/OPTIMIZE` cỡ large hoặc profile mạnh hơn `standard`, mặc định thêm reviewer lane độc lập; với `BUILD` có `spec-review`, nghiêng về pipeline `implementer -> spec-reviewer -> quality-reviewer`.
**Lane model policy:** dùng tier trừu tượng `cheap / standard / capable` theo lane thay vì đẩy mọi bước lên cùng một mức năng lực.

**Domain skills** (`frontend`, `backend`) thêm vào khi task liên quan UI hoặc API/database/service layer.
**Companion runtime/language skills** (Python, Java, Go, .NET, framework-specific) là optional augmentation khi repo/framework đã rõ. Forge vẫn phải chạy tốt nếu không có chúng.
Contract ghép companion skill: xem `references/companion-skill-contract.md` khi bạn thật sự đang thêm runtime/framework layer.
Nếu workspace có `AGENTS.md` hoặc router doc trỏ tới local skills, dùng router đó như source-of-truth cho lớp mở rộng này; nếu không có, Forge vẫn tiếp tục bằng chính bundle của nó.
Muốn preview deterministic cho một prompt cụ thể: chạy `scripts/route_preview.py`.

### Cách load skill

```
1. Detect intent + complexity
2. Tra matrix -> danh sách Forge skills cần dùng
3. Chọn execution pipeline và lane model tiers nếu task đủ lớn/rủi ro
4. Chọn chain Forge đủ để giải quyết task bằng chính bundle này
5. Kiểm repo signals (`package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, ...)
6. Nếu có companion skill phù hợp và thật sự giúp tăng độ chính xác -> thêm vào chain
7. Nếu workspace có router doc cho local skills -> dùng nó như layer mở rộng, không thay Forge
8. Thông báo user: "Forge: [intent] | [complexity] | Skills: [list]"
9. Load skill đầu tiên
10. Hoàn thành quality gate quan trọng
11. Mới chuyển sang skill tiếp theo nếu cần
```

Không cần load đầy đủ đường dây nếu task đã được giải quyết an toàn ở sớm hơn.
Companion/local skill không được override verification/evidence gate của Forge.

**Minimal routing policy:** với `REVIEW`, `SESSION`, và task `small`, Forge ưu tiên prompt-led routing. Repo signals lúc này không được tự động kéo thêm domain skills, local companions, hay escalation profile nếu prompt không nêu rõ nhu cầu.

---

## Verification Strategy

Áp dụng cho mọi intent có sửa đổi:

- **Behavioral code change + có harness** -> ưu tiên failing test hoặc reproduction trước khi sửa.
- **Behavioral code change + không có harness khả thi** -> tạo manual reproduction, failing command, hoặc smoke scenario rõ ràng trước khi sửa.
- **Non-behavioral change** (`docs`, `config`, `build script`, `release chores`) -> chốt verification command trước khi edit: build, lint, typecheck, diff, hoặc smoke run.

Không fake TDD nếu project không có harness. Không bỏ qua verification nếu harness không có.
Verification profiles canonical sống trong `data/orchestrator-registry.json`.

## Execution Upgrade Notes

- Forge dùng `execution pipeline` để tránh vừa implement vừa tự review cùng một lane.
- Forge dùng `lane model tiers` để tối ưu cost: navigation/triage có thể rẻ hơn spec-review hoặc release gates.
- Forge dùng `quality-gate` như canonical source cho evidence response contract và anti-rationalization.
- `spec-review` loop bị chặn tối đa `3` vòng revise cho cùng một packet; quá ngưỡng này phải `blocked`.

---

## Skill Registry

| Skill | File | Type | Iron Law |
|-------|------|------|----------|
| brainstorm | `workflows/design/brainstorm.md` | flexible | NO AMBIGUOUS MEDIUM/LARGE WORK WITHOUT CHOOSING A DIRECTION FIRST |
| plan | `workflows/design/plan.md` | flexible | NO MEDIUM/LARGE BUILD WITHOUT A CONFIRMED PLAN |
| architect | `workflows/design/architect.md` | flexible | NO LARGE IMPLEMENTATION WITHOUT ARCHITECTURE DECISIONS DOCUMENTED |
| spec-review | `workflows/design/spec-review.md` | rigid | NO HIGH-RISK BUILD WITHOUT A BUILD-READINESS REVIEW FIRST |
| build | `workflows/execution/build.md` | rigid | NO BEHAVIORAL CHANGE WITHOUT DEFINING VERIFICATION FIRST |
| frontend | `domains/frontend.md` | flexible | PRESERVE THE EXISTING DESIGN SYSTEM BEFORE INVENTING A NEW ONE |
| backend | `domains/backend.md` | flexible | VALIDATE AT THE BOUNDARY, KEEP LOGIC OUT OF TRANSPORT |
| debug | `workflows/execution/debug.md` | rigid | NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION |
| test | `workflows/execution/test.md` | rigid | USE FAILING TESTS FIRST WHEN A HARNESS EXISTS |
| secure | `workflows/execution/secure.md` | rigid | NO RELEASE WITHOUT EXPLICIT SECURITY REVIEW |
| deploy | `workflows/execution/deploy.md` | rigid | NO DEPLOY WITHOUT VERIFIED QUALITY GATES |
| quality-gate | `workflows/execution/quality-gate.md` | rigid | NO CLAIMS, HANDOFFS, OR DEPLOYS WITHOUT A FRESH GO / NO-GO DECISION |
| review | `workflows/execution/review.md` | flexible | FINDINGS FIRST, SUMMARY SECOND |
| refactor | `workflows/execution/refactor.md` | rigid | NO REFACTOR WITHOUT BASELINE AND AFTER VERIFICATION |
| visualize | `workflows/design/visualize.md` | flexible | DO NOT CODE UI BEFORE THE INTERACTION MODEL IS CLEAR |
| session | `workflows/execution/session.md` | flexible | REBUILD CONTEXT FROM REAL ARTIFACTS BEFORE WRITING MEMORY |
| help | `workflows/operator/help.md` | flexible | REPO-FIRST GUIDANCE, NOT RECAP THEATER |
| next | `workflows/operator/next.md` | flexible | ONE CONCRETE NEXT STEP, NOT VAGUE MOMENTUM TALK |
| run | `workflows/operator/run.md` | flexible | EXECUTE THE REAL COMMAND, THEN ROUTE FROM EVIDENCE |
| bump | `workflows/operator/bump.md` | flexible | VERSION BUMPS MUST BE USER-REQUESTED, JUSTIFIED, AND MUST SURFACE RELEASE VERIFICATION |
| rollback | `workflows/operator/rollback.md` | flexible | DO NOT BLINDLY ROLL BACK WITHOUT SCOPE, RISK, AND POST-ROLLBACK VERIFICATION |
| customize | `workflows/operator/customize.md` | flexible | DO NOT FORK THE CORE PREFERENCES SCHEMA OR WRITE HOST-LOCAL KEYS |
| init | `workflows/operator/init.md` | flexible | DO NOT OVERWRITE EXISTING REPO FILES DURING BOOTSTRAP |
| recap | `workflows/operator/recap.md` | flexible | RESTORE FROM REPO FIRST, MEMORY SECOND |
| save-brain | `workflows/operator/save-brain.md` | flexible | SAVE ONLY DURABLE, SCOPED CONTINUITY |
| handover | `workflows/operator/handover.md` | flexible | CAPTURE ONLY THE NEXT PERSON ACTUALLY NEEDS |

**Rigid skills:** không bỏ qua evidence và quality gate.  
**Flexible skills:** adapt theo context, nhưng vẫn phải rõ output và next step.

---

## Global Resilience

### Auto-Retry
```
Lỗi network, timeout, file write:
1. Retry lần 1
2. Retry lần 2 nếu lỗi có vẻ tạm thời
3. Vẫn fail -> thông báo user + đề xuất fallback
```

### Long-Running Work
```
Nếu task kéo dài hoặc command lặp lại thất bại:
1. Báo user đang kẹt ở đâu
2. Tóm tắt đã thử gì
3. Đề xuất bước tiếp theo an toàn nhất
```

### Error Translation (khi cần)

| Lỗi gốc | Dịch |
|---------|------|
| `ECONNREFUSED` | Dịch vụ hoặc database chưa bật |
| `Cannot read undefined` | Đang đọc dữ liệu chưa tồn tại |
| `Module not found` | Thiếu package hoặc đường dẫn import sai |
| `CORS error` | Server đang chặn request từ origin này |
| `401 Unauthorized` | Chưa đăng nhập hoặc token hết hạn |
| `Hydration mismatch` | HTML server và client render khác nhau |

---

## Golden Rules

```
1. CHỈ LÀM ĐÚNG YÊU CẦU - Không tự mở rộng scope
2. MỘT VIỆC MỘT LÚC - Chốt xong A mới nhảy sang B
3. THAY ĐỔI TỐI THIỂU - Sửa đúng chỗ cần sửa
4. XIN PHÉP VIỆC LỚN - Schema, folder structure, dependency mới -> hỏi trước
5. EVIDENCE BEFORE CLAIMS - Verify trước khi nói "xong"
```

## Reference Map

Điểm vào nhanh cho references: xem `references/reference-map.md`.

## Activation Announcement

```
Forge Antigravity: orchestrator | route đúng intent, giữ evidence trước claims
```
