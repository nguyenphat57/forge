# Forge Reference Map

> Mục tiêu: giúp người bảo trì và agent biết nên đọc reference nào cho đúng việc, thay vì lục toàn bộ thư mục `references/`.

## Reference Registry

| File | Khi nào đọc |
|------|-------------|
| `smoke-tests.md` | Smoke test host routing và behavior chung của Forge |
| `smoke-test-checklist.md` | Ghi kết quả chạy smoke test từng case |
| `backend-briefs.md` | Tạo hoặc reuse backend brief cho API/job/event/data change ở mức vừa/lớn |
| `execution-delivery.md` | Chọn execution mode, checkpoint, và completion state cho build lớn |
| `failure-recovery-playbooks.md` | Khi chain bị stalled, gate bị blocked, review deadlock, hoặc deploy fail cần đường ra rõ |
| `ui-briefs.md` | Khi frontend/visualize cần first artifact trước khi code hoặc mockup |
| `frontend-stack-profiles.md` | Chọn stack lens cho frontend hoặc visualize |
| `ui-quality-checklist.md` | Review nhanh anti-patterns và delivery checklist cho UI work |
| `ui-escalation.md` | Quyết định khi nào cần kéo thêm `$ui-ux-pro-max` |
| `ui-good-bad-examples.md` | Mẫu đúng/sai để giảm agent phải tự suy luận anti-pattern |
| `ui-heuristics.md` | Heuristics global cho touch-heavy, dashboard, dense-data UI |
| `ui-progress.md` | Track stage cho task UI kéo dài |
| `tooling.md` | Khi cần chạy route preview, capture continuity, router checker, hoặc tìm artifact paths |
| `personalization.md` | Khi sửa response-style preferences, adaptive language, hoặc adapter wrappers cho customize |
| `help-next.md` | Khi sửa navigator logic cho help/next, repo-state priority, hoặc operator guidance wrappers |
| `run-guidance.md` | Khi sửa workflow `run`, ready-signal detection, command classification, hoặc adapter wrappers cho execute-then-route |
| `error-translation.md` | Khi sửa error pattern database, sanitation rules, hoặc cách `run/debug/test` đổi lỗi kỹ thuật thành guidance đọc được |
| `bump-release.md` | Khi sửa version-bump checklist, semver math, hoặc release artifact update flow |
| `rollback-guidance.md` | Khi sửa rollback planner, risk framing, hoặc recovery strategy selection |
| `canary-rollout.md` | Khi cần rollout Forge trên workspace thật và chốt readiness bằng canary artifacts |
| `companion-skill-contract.md` | Thiết kế hoặc update companion skills, khi repo thật sự có lớp runtime/framework mở rộng |
| `companion-routing-smoke-tests.md` | Kiểm routing giữa Forge và companion skills, chỉ khi dùng companion/local layer |

## Reading Order

### Khi maintain Forge core

```text
1. SKILL.md
2. tooling.md nếu cần deterministic preview/check thay vì đọc prose thuần
3. personalization.md nếu đang sửa response style hay preference engine
4. help-next.md nếu đang sửa navigator help/next
5. run-guidance.md nếu đang sửa run/execute-then-route
6. error-translation.md nếu đang sửa error translator/helper layer
7. bump-release.md hoặc rollback-guidance.md nếu đang sửa release operators
8. backend-briefs.md hoặc execution-delivery.md tùy layer đang sửa
9. smoke-tests.md / smoke-test-checklist.md nếu cần verify host behavior
10. canary-rollout.md nếu đang chuẩn bị rollout thật
11. companion-skill-contract.md chỉ khi đang sửa lớp companion/runtime
12. companion-routing-smoke-tests.md chỉ khi đang test lớp companion/runtime
```

### Khi repo chưa có local skills

```text
1. SKILL.md
2. plan.md / architect.md / build.md / debug.md / review.md tùy intent
3. backend-briefs.md hoặc ui-briefs.md nếu task cần first artifact
4. execution-delivery.md hoặc quality-gate.md nếu task dài hoặc rủi ro
```

### Khi chỉ muốn smoke test Forge core

```text
1. smoke-tests.md
2. smoke-test-checklist.md
3. canary-rollout.md nếu smoke này là một phần của rollout thật
```

### Khi debug companion routing

```text
1. companion-skill-contract.md
2. companion-routing-smoke-tests.md
3. tooling.md nếu cần chạy checker
4. canary-rollout.md nếu bug đang xuất hiện ở workspace thật
```

### Khi thiết kế workspace theo mô hình global + local

```text
1. companion-skill-contract.md
2. tooling.md
3. companion-routing-smoke-tests.md
4. smoke-tests.md nếu cần verify host behavior rộng hơn
5. canary-rollout.md nếu đang làm rollout có kiểm soát
```

### Khi làm implementation sau plan/design

```text
1. execution-delivery.md
2. failure-recovery-playbooks.md nếu chain có risk stall/block
3. tooling.md nếu cần checkpoint artifact
4. build.md
5. review.md nếu cần clear disposition sau cùng
6. quality-gate.md nếu cần go/no-go rõ trước claim hoặc deploy
```

### Khi làm release-critical flow

```text
1. secure.md
2. quality-gate.md
3. deploy.md
4. failure-recovery-playbooks.md nếu gate bị block hoặc rollout fail
5. execution-delivery.md nếu chain dài hoặc high-risk
```

### Khi làm backend

```text
1. backend-briefs.md
2. tooling.md nếu muốn generate/check/persist backend brief
3. backend.md
4. failure-recovery-playbooks.md nếu task là migration/recovery/high-risk
5. execution-delivery.md nếu task backend kéo dài qua nhiều checkpoint
6. companion-skill-contract.md nếu runtime/framework đã rõ và muốn ghép thêm layer
```

### Khi làm frontend hoặc visualize

```text
1. ui-briefs.md
2. frontend-stack-profiles.md
3. ui-quality-checklist.md
4. ui-good-bad-examples.md
5. ui-heuristics.md
6. ui-escalation.md nếu visual direction còn quá mở
7. ui-progress.md nếu task kéo dài
8. tooling.md nếu muốn generate/check/track/persist bằng script
```

### Khi stalled hoặc blocked

```text
1. failure-recovery-playbooks.md
2. execution-delivery.md nếu cần nhìn lại chain/checkpoint
3. tooling.md nếu cần capture artifact mới
4. debug.md / quality-gate.md / review.md / deploy.md tùy chỗ đang kẹt
5. canary-rollout.md nếu kẹt ở phase rollout thật
```
