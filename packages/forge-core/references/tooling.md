# Forge Tooling

> Dùng khi muốn biến routing/verification của Forge từ prose sang bước kiểm tra có thể chạy được.

## Registry Canonical Source

- File machine-readable của orchestrator nằm tại `data/orchestrator-registry.json`
- Đây là nguồn canonical cho:
- intent keywords
- skill composition matrix
- complexity hints
- verification profiles
- runtime hints
- execution modes
- execution pipelines
- lane model policy
- evidence response contract
- completion states

## Preferences Resolver

Khi cần inspect hoặc validate response-style preferences theo schema chung của Forge:

```powershell
python scripts/resolve_preferences.py --workspace C:\path\to\workspace
```

Explicit file:

```powershell
python scripts/resolve_preferences.py --preferences-file C:\path\to\.brain\preferences.json --format json
```

Strict validation:

```powershell
python scripts/resolve_preferences.py --workspace C:\path\to\workspace --strict
```

Script sẽ trả về:
- source của preferences (explicit, workspace-local, hoặc defaults)
- canonical preferences sau khi normalize
- response-style contract đã resolve
- warnings nếu payload có field lạ hoặc giá trị không hợp lệ

Schema và boundary doc: xem `personalization.md`.

## Preferences Persistence

Khi cần update `.brain/preferences.json` mà vẫn giữ schema canonical của Forge:

```powershell
python scripts/write_preferences.py --workspace C:\path\to\workspace --technical-level newbie --pace fast
python scripts/write_preferences.py --workspace C:\path\to\workspace --feedback-style direct --apply
```

Script sẽ:
- merge update vào preferences hiện có theo mặc định
- hỗ trợ `--replace` để reset field không truyền về defaults
- trả về `changed_fields`, target preferences, và response-style contract sau khi normalize

Semantics chi tiết: xem `personalization.md`.

## Workspace Init

Khi cần preview hoặc tạo skeleton Forge tối thiểu cho workspace mới:

```powershell
python scripts/initialize_workspace.py --workspace C:\path\to\workspace
python scripts/initialize_workspace.py --workspace C:\path\to\workspace --seed-preferences --apply
```

Script sẽ:
- classify workspace thành `greenfield` hoặc `existing`
- tạo `.brain/`, `docs/plans/`, `docs/specs/`, và `.brain/session.json`
- tùy chọn seed `.brain/preferences.json`
- trả về next workflow khuyến nghị (`brainstorm` hoặc `plan`)

Semantics chi tiết: xem `workspace-init.md`.

## Help/Next Navigator

Khi cần resolve operator guidance dựa trên repo state thay vì recap ritual:

```powershell
python scripts/resolve_help_next.py --workspace C:\path\to\workspace --mode help
python scripts/resolve_help_next.py --workspace C:\path\to\workspace --mode next --format json
```

Script se doc:
- `git status` nếu workspace đó là git root riêng
- `docs/plans/` va `docs/specs/`
- `.brain/session.json` và `.brain/handover.md` nếu có
- `README`
- `.brain/preferences.json` de adapt response style

Script se tra ve:
- `current_stage`
- `current_focus`
- `suggested_workflow`
- `recommended_action`
- tối đa 2 alternatives
- evidence va warnings

Semantics chi tiet: xem `help-next.md`.

## Run Guidance

Khi cần chạy lệnh thật và route bước tiếp theo từ output:

```powershell
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
```

Script sẽ trả về:
- `state`
- `command_kind`
- `suggested_workflow`
- `recommended_action`
- `stdout_excerpt` / `stderr_excerpt`
- `readiness_detected`
- evidence va warnings

Nếu dùng `--persist`, artifact mặc định nằm ở:

```text
.forge-artifacts/run-reports/
```

Semantics chi tiết: xem `run-guidance.md`.

## Error Translation

Khi cần dịch stderr/raw error sang tóm tắt dễ đọc hơn mà vẫn giữ đủ context cho debug:

```powershell
python scripts/translate_error.py --error-text "Module not found: payments.service"
python scripts/translate_error.py --input-file C:\path\to\stderr.txt --format json
```

Script sẽ:
- sanitize token, secret, và path nhạy cảm cơ bản
- match vào pattern database deterministic
- trả về `human_message`, `suggested_action`, và `category`
- fallback generic nếu chưa có pattern phù hợp

Semantics chi tiết: xem `error-translation.md`.

## Bump Preparation

Khi cần chốt version mới theo explicit release flow:

```powershell
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump minor
python scripts/prepare_bump.py --workspace C:\path\to\workspace --bump 2.0.0 --apply --release-ready
```

Script sẽ:
- đọc `VERSION`
- tính `target_version`
- preview hoặc update `VERSION` + `CHANGELOG.md`
- trả về verification commands kế tiếp

Semantics chi tiết: xem `bump-release.md`.

## Rollback Guidance

Khi cần plan rollback an toàn thay vì blind-revert:

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high
```

Script se:
- chot recovery strategy theo scope/risk
- cảnh báo data-loss risk khi cần
- tra ve suggested workflow va verification checklist

Semantics chi tiet: xem `rollback-guidance.md`.

## UI Brief Generator

Khi task là `frontend` hoặc `visualize` và cần first artifact rõ trước khi code/mockup:

```powershell
python scripts/generate_ui_brief.py "Refresh checkout for tablet POS" `
  --mode frontend `
  --stack react-vite `
  --platform tablet `
  --screen checkout
```

Hoặc:

```powershell
python scripts/generate_ui_brief.py "Explore calmer kitchen dashboard direction" `
  --mode visualize `
  --stack mobile-webview `
  --platform tablet `
  --screen kitchen-dashboard
```

### Persist UI brief

```powershell
python scripts/generate_ui_brief.py "..." --mode frontend --persist --project-name "LamDiFood POS" --screen checkout
```

Artifact mặc định:

```text
.forge-artifacts/ui-briefs/<project-slug>/<mode>/
```

Chi tiết brief pattern: xem `ui-briefs.md`.

## Backend Brief Generator

Khi task backend là medium/large hoặc chạm contract/schema/job/event:

```powershell
python scripts/generate_backend_brief.py "Add bulk order cancellation endpoint" `
  --pattern sync-api `
  --runtime node-service `
  --surface cancel-orders
```

Hoặc:

```powershell
python scripts/generate_backend_brief.py "Reconcile failed payouts in worker" `
  --pattern async-job `
  --runtime python-service `
  --surface payout-reconcile
```

### Persist backend brief

```powershell
python scripts/generate_backend_brief.py "..." --pattern sync-api --persist --project-name "Example Project" --surface cancel-orders
```

Artifact mặc định:

```text
.forge-artifacts/backend-briefs/<project-slug>/
```

Chi tiết brief pattern: xem `backend-briefs.md`.

## Backend Brief Checker

Khi brief backend đã được persist và cần verify nhanh:

```powershell
python scripts/check_backend_brief.py .forge-artifacts/backend-briefs/<project-slug> --surface cancel-orders
```

Artifact report mặc định:

```text
.forge-artifacts/backend-brief-checks/
```

## UI Brief Checker

Khi brief đã được persist và cần verify nhanh rằng artifact đủ section bắt buộc:

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
```

Artifact report mặc định:

```text
.forge-artifacts/ui-brief-checks/
```

## UI Progress Tracker

Khi task frontend/visualize kéo dài qua nhiều stage:

```powershell
python scripts/track_ui_progress.py "Checkout tablet refresh" --mode frontend --stage implementation --status active
```

Artifact mặc định:

```text
.forge-artifacts/ui-progress/<mode>/
```

## Route Preview

Khi muốn preview route cho một prompt trước khi load skill chain:

```powershell
python scripts/route_preview.py "Fix outbox bi ket sau khi app online lai" `
  --repo-signal package.json `
  --repo-signal src/services/syncManager.ts
```

Nếu workspace có local layer, thêm `--workspace-router` như input tùy chọn:

```powershell
python scripts/route_preview.py "..." `
  --workspace-router C:\path\to\workspace\.agent\workspace-skill-map.md
```

`--workspace-router` chấp nhận cả `AGENTS.md` lẫn router map đã resolve.

Script sẽ trả về:
- intent
- complexity
- Forge skills
- execution mode recommendation
- execution pipeline recommendation
- lane model tier recommendations
- quality profile recommendation
- domain skills
- local companion candidates (nếu workspace có local layer)
- verification-first plan

Với `REVIEW`, `SESSION`, và task `small`, preview ưu tiên minimal path: repo signals không tự động kéo thêm domain/local companions nếu prompt không nói rõ.

### Persist route preview

```powershell
python scripts/route_preview.py "..." --persist
```

Artifact mặc định:

```text
.forge-artifacts/route-previews/
```

Ví dụ high-risk build:

```powershell
python scripts/route_preview.py "Implement auth migration with public API contract change" `
  --repo-signal package.json `
  --repo-signal migrations `
  --repo-signal api/
```

Kỳ vọng output:
- `Execution pipeline: Implementer -> spec reviewer -> quality reviewer`
- `Lane model tiers`
- `Spec-review loop cap: 3` khi applicable

## Scoped Continuity Capture

Khi có decision hoặc learning đủ bền để lưu theo scope:

```powershell
python scripts/capture_continuity.py "Compatibility window phải giữ 1 release" `
  --kind decision `
  --scope orders-api `
  --evidence "docs/DESIGN.md"
```

Artifact mặc định:

```text
.brain/decisions.json
.brain/learnings.json
```

## Execution Progress Tracker

Khi build task medium/large kéo dài qua nhiều checkpoint:

```powershell
python scripts/track_execution_progress.py "Implement offline order reconciliation" `
  --mode checkpoint-batch `
  --stage integration `
  --lane implementer `
  --model-tier capable `
  --proof "failing reconciliation reproduction" `
  --status active `
  --done "Added reconciliation service skeleton" `
  --next "Wire retry policy into sync manager" `
  --risk "End-to-end verification still pending"
```

Persist artifact:

```powershell
python scripts/track_execution_progress.py "..." --mode checkpoint-batch --stage integration --persist --project-name "Example Project"
```

Artifact mặc định:

```text
.forge-artifacts/execution-progress/<project-slug>/
```

Fields mới quan trọng:
- `lane`
- `model-tier`
- `proof-before-progress`

## Chain Status Tracker

Khi chain dài đi qua nhiều skill/stage và cần thấy trạng thái tổng:

```powershell
python scripts/track_chain_status.py "Checkout rewrite flow" `
  --project-name "Example Project" `
  --current-stage spec-review `
  --completed-stage brainstorm `
  --completed-stage plan `
  --next-stage build `
  --active-skill build `
  --active-skill spec-review `
  --active-lane implementer `
  --active-lane spec-reviewer `
  --lane-model implementer=capable `
  --lane-model spec-reviewer=capable `
  --review-iteration 2 `
  --max-review-iterations 3 `
  --gate-decision conditional `
  --risk "Large migration verification still pending"
```

Persist artifact:

```powershell
python scripts/track_chain_status.py "..." --current-stage build --persist --project-name "Example Project"
```

Artifact mặc định:

```text
.forge-artifacts/chain-status/<project-slug>/
```

Fields mới quan trọng:
- `active-lanes`
- `lane-model`
- `review-iteration`
- `max-review-iterations`

## Workspace Router Check

Chỉ dùng khi workspace thật sự có local skill layer hoặc router docs.

Khi vừa sửa `AGENTS.md`, workspace map, hoặc local skills:

```powershell
python scripts/check_workspace_router.py C:\path\to\workspace
```

Checker sẽ so:
- `AGENTS.md`
- workspace skill map
- local skills dưới `.agent/skills/`
- routing smoke tests
- local-skill maintenance doc

### Persist router check

```powershell
python scripts/check_workspace_router.py C:\path\to\workspace --persist
```

Artifact mặc định:

```text
.forge-artifacts/router-checks/
```

## Regression Tests

Khi vừa đổi routing logic, companion detection, hoặc router checker:

```powershell
python -m unittest discover -s tests -v
```

Hiện regression suite tập trung vào:
- route preview cho review/session/local-companion cases
- workspace router checker cho explicit router doc names

## Smoke Matrix Runner

Khi cần chạy smoke cases thực thi được thay vì chỉ đọc checklist:

```powershell
python scripts/run_smoke_matrix.py
```

Tùy chọn:

```powershell
python scripts/run_smoke_matrix.py --suite route-preview
python scripts/run_smoke_matrix.py --suite router-check --format json
```

Runner này đọc fixture từ `tests/fixtures/` và gọi chính CLI scripts để bắt drift ở mức entrypoint.
Smoke suite hiện cover:
- route preview
- workspace router check
- preferences resolution
- help/next navigator
- run guidance
- error translation
- bump preparation
- rollback guidance

## Verify Bundle

Lệnh release/CI chuẩn cho Forge bundle:

```powershell
python scripts/verify_bundle.py
```

Pipeline hiện tại:
- `py_compile` cho scripts + tests
- `unittest discover -s tests -v`
- `run_smoke_matrix.py`

Nếu đã có soak/canary artifacts thật:

```powershell
python scripts/verify_bundle.py --include-canary --canary-profile controlled-rollout
python scripts/verify_bundle.py --include-canary --canary-profile broad
```

## Canary Rollout Tooling

Chạy canary pack tự động trên workspace thật:

```powershell
python scripts/run_workspace_canary.py C:\path\to\workspace --persist
```

Runner này sẽ:
- detect repo signals thông dụng
- chạy core route pack (`review`, `session`, `build`, `debug`, `deploy`)
- chạy router check nếu workspace có `AGENTS.md`
- chạy runtime-signal local companion check nếu workspace có local skills
- persist cả detail artifact lẫn canary-run summary

Ghi một canary run:

```powershell
python scripts/record_canary_result.py "Core prompts stable on POS workspace" `
  --workspace lamdi-pos `
  --status pass `
  --scenario "review route" `
  --persist
```

Đánh giá readiness:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile broad
```

Broad readiness hiện cũng đòi ít nhất 2 ngày quan sát khác nhau, không chỉ đủ số run.

Runbook chi tiết: xem `canary-rollout.md`.

## Khi nào dùng tool nào

- Preview một task đơn lẻ: `route_preview.py`
- Audit drift của workspace router: `check_workspace_router.py` khi workspace có local layer
- Capture decision/learning scoped, evidence-backed: `capture_continuity.py`
- Tạo hoặc check first artifact cho backend: `generate_backend_brief.py` / `check_backend_brief.py`
- Check chain/go-no-go tổng thể: `track_chain_status.py` + `quality-gate.md`
- Track checkpoint cho build dài: `track_execution_progress.py`
- Track toàn chain dài: `track_chain_status.py`
- Chạy smoke suite entrypoint-level: `run_smoke_matrix.py`
- Chạy full release gate cục bộ/CI: `verify_bundle.py`
- Chạy canary pack tự động trên workspace thật: `run_workspace_canary.py`
- Ghi soak/canary artifact từ workspace thật: `record_canary_result.py`
- Chốt verdict rollout từ artifact thật: `evaluate_canary_readiness.py`
- Chỉ đọc policy và examples: quay lại `SKILL.md` hoặc `references/companion-skill-contract.md`
