# Forge Canary Rollout

> Mục tiêu: biến câu hỏi "đã production-ready chưa?" thành một canary gate có artifact, ngưỡng rõ, và verdict lặp lại được.

## Khi nào đọc file này

- Khi Forge core đã pass `verify_bundle.py` nhưng bạn còn thiếu bằng chứng vận hành trên host thật
- Khi chuẩn bị rollout Forge cho 2-3 workspace đầu tiên
- Khi cần chốt `controlled-rollout ready` hoặc `broad ready`

## Rollout Stages

### 1. Controlled Rollout

Mục tiêu:
- Ít nhất 2 workspaces thật
- Ít nhất 1 ngày quan sát
- Không có run `fail`
- Tối đa 1 workspace đang ở trạng thái `warn`
- Không còn blocker ở latest run

Lệnh đánh giá:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
```

### 2. Broad Readiness

Mục tiêu:
- Ít nhất 3 workspaces thật
- Ít nhất 6 canary runs tổng
- Ít nhất 2 ngày quan sát khác nhau
- Không có run `fail`
- Không có workspace latest run ở trạng thái `warn`
- Không còn blocker ở latest run

Lệnh đánh giá:

```powershell
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile broad
```

## Workspace Selection

Ưu tiên 3 loại workspace:
- 1 workspace có local router/companion layer
- 1 workspace chủ yếu dùng Forge core, không có local layer
- 1 workspace có flow high-risk hơn: build/debug/deploy/review đan xen

Không chọn cả 3 workspace cùng một shape; mục tiêu là bắt misroute và fallback behavior trên bề mặt khác nhau.

## Scenario Pack Gợi Ý

Mỗi workspace nên chạy ít nhất:
- review natural-language
- session/continue natural-language
- build medium hoặc large
- debug regression-style
- deploy readiness

Nếu workspace có local companions:
- runtime-signal-only selection
- router checker sau khi đổi docs/local skill inventory

## Canonical Workspace Runner

Ưu tiên dùng runner tự động trước, rồi mới bổ sung `record_canary_result.py` khi cần note manual:

```powershell
python scripts/run_workspace_canary.py C:\path\to\workspace --persist
```

Runner tự persist:
- `.forge-artifacts/workspace-canaries/`
- `.forge-artifacts/canary-runs/`

## Cách ghi một canary run

```powershell
python scripts/record_canary_result.py "Core prompts stable on POS workspace" `
  --workspace lamdi-pos `
  --status pass `
  --scenario "review route" `
  --scenario "build checkout flow" `
  --signal "No misroute seen across 12 prompts" `
  --follow-up "Repeat after next routing change" `
  --persist
```

Nếu có cảnh báo:

```powershell
python scripts/record_canary_result.py "1 warn on companion fallback wording" `
  --workspace kitchen-display `
  --status warn `
  --scenario "python companion selection" `
  --signal "Route correct but explanation still generic" `
  --follow-up "Tighten activation phrasing" `
  --persist
```

Nếu có blocker:

```powershell
python scripts/record_canary_result.py "Router drift broke local skill selection" `
  --workspace ops-console `
  --status fail `
  --scenario "router check after inventory change" `
  --blocker "Local skill missing from router map" `
  --follow-up "Fix router map and rerun canary" `
  --persist
```

## Canonical Gate

Trước khi nói Forge "production-ready":

```powershell
python scripts/verify_bundle.py
python scripts/evaluate_canary_readiness.py .forge-artifacts/canary-runs --profile controlled-rollout
```

Khi muốn chốt rộng hơn:

```powershell
python scripts/verify_bundle.py --include-canary --canary-profile broad
```

## Verdict Language

Chỉ dùng 1 trong 3 verdict:
- `not-ready`: verify bundle fail hoặc canary profile fail
- `controlled-rollout ready`: verify bundle pass + canary controlled-rollout pass
- `broad ready`: verify bundle pass + canary broad pass

Không dùng câu mơ hồ kiểu:
- "gần như production"
- "chắc ổn rồi"
- "về cơ bản dùng được"

## Failure Handling

Nếu canary fail:
1. Ghi artifact bằng `record_canary_result.py`
2. Fix drift hoặc blocker trong bundle
3. Chạy lại `verify_bundle.py`
4. Rerun workspace canary bị fail
5. Chỉ nâng verdict khi latest run đã sạch
