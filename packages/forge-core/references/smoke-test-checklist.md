# Forge Smoke Test Checklist

Mục tiêu: ghi kết quả nhanh cho từng lần chạy smoke test trong host thật đang rollout Forge.

## Metadata

| Trường | Giá trị |
|--------|---------|
| Ngày test | |
| Người test | |
| Workspace / project | |
| Host version | |
| Forge bundle version / commit | |
| Ghi chú chung | |

## Thang chấm

- `PASS`: route đúng, guardrail đúng, output usable
- `WARN`: route đúng nhưng evidence hoặc output chưa đủ sắc
- `FAIL`: route sai, bỏ guardrail, hoặc claim không có bằng chứng

## Checklist tổng

| Hạng mục | PASS/WARN/FAIL | Ghi chú |
|----------|----------------|---------|
| Không bịa token/context telemetry | |
| Repo-first trước `.brain` khi phù hợp | |
| Review trả findings trước summary | |
| Build/debug giữ evidence-first | |
| Evidence response contract được giữ | |
| Execution pipeline/lane stance rõ khi task đủ lớn | |
| Generic repo signals không kéo domain sai | |
| Spec-review loop không revise vô hạn | |
| Session không biến `/save-brain` thành ritual | |
| Không có route sai rõ ràng | |

## Kết quả theo test case

### FT-01: Restore nhanh

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/recap` |
| Route đúng skill? | |
| Repo-first? | |
| Có lạm dụng `.brain` không? | |
| Mức chấm | |
| Ghi chú | |

### FT-02: Restore sâu

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/recap full` |
| Route đúng skill? | |
| Restore có rộng hơn FT-01 không? | |
| Repo-first? | |
| Mức chấm | |
| Ghi chú | |

### FT-03: Resume tự nhiên

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `Tiếp tục việc hôm trước, nhắc nhanh mình đang làm gì và bước hợp lý tiếp theo.` |
| Route đúng skill? | |
| Có yêu cầu user gõ `/recap` lại không? | |
| Next step có actionable không? | |
| Mức chấm | |
| Ghi chú | |

### FT-04: Plan medium task

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/plan` + yêu cầu loyalty point |
| Route đúng skill? | |
| Có chốt scope/assumptions không? | |
| Có tránh nhảy vào code không? | |
| Mức chấm | |
| Ghi chú | |

### FT-05: Build task có behavior

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/code` + yêu cầu export CSV |
| Route đúng skill? | |
| Có nêu verification strategy trước khi sửa không? | |
| Có execution pipeline/lane stance rõ không? | |
| Có nói rõ harness / verify thay thế không? | |
| Có tránh performative agreement không? | |
| Mức chấm | |
| Ghi chú | |

### FT-06: Debug task

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/debug` + lỗi crash màn hình thanh toán |
| Route đúng skill? | |
| Có đi theo root cause trước fix không? | |
| Có chốt execution pipeline/lane stance khi debug đủ lớn không? | |
| Có tránh đoán mò không? | |
| Có dùng evidence response contract không? | |
| Mức chấm | |
| Ghi chú | |

### FT-06B: Spec-review bounded loop

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | build large/high-risk có spec còn hở |
| Có route qua `spec-review` không? | |
| Có chỉ ra iteration hiện tại không? | |
| Có block sau ngưỡng revise tối đa không? | |
| Mức chấm | |
| Ghi chú | |

### FT-06C: Debug reviewer lane

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/debug` + regression sau release qua nhiều boundary |
| Có route theo `implementer -> quality-reviewer` không? | |
| Reviewer lane có challenge root cause/evidence không? | |
| Có escalate sang `plan/architect` khi boundary chưa rõ không? | |
| Mức chấm | |
| Ghi chú | |

### FT-07: Review task

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/review` + review thay đổi hiện tại |
| Route đúng skill? | |
| Findings có lên trước không? | |
| Có note assumptions/testing gaps không? | |
| Mức chấm | |
| Ghi chú | |

### FT-08: Visualize task

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/visualize` + checkout tablet |
| Route đúng skill? | |
| Có chốt interaction model trước code không? | |
| Có output wireframe/spec usable không? | |
| Mức chấm | |
| Ghi chú | |

### FT-09: Deploy readiness

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/deploy` + kiểm tra production readiness |
| Route đúng skill? | |
| Có pre-deploy/security/rollback không? | |
| Gate 2 có đi theo syntax/config -> type/lint -> build entry không? | |
| Có tránh claim bằng lời không? | |
| Mức chấm | |
| Ghi chú | |

### FT-09B: Route preview lane policy

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | high-risk build/deploy prompt qua `route_preview.py` |
| Có hiện execution pipeline không? | |
| Có hiện lane model tiers không? | |
| Có hiện spec-review loop cap khi applicable không? | |
| Mức chấm | |
| Ghi chú | |

### FT-09C: Route preview domain sanity

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | debug/regression prompt + generic `src/` repo signal |
| Không tự gắn `frontend` chỉ vì `src/` không? | |
| Vẫn gắn domain đúng khi có prompt/signal mạnh hơn không? | |
| Mức chấm | |
| Ghi chú | |

### FT-10: Save progress

| Mục | Kết quả |
|-----|---------|
| Prompt đã chạy | `/save-brain` |
| Route đúng skill? | |
| Nội dung save có gọn và hữu ích không? | |
| Có tránh ritual dài dòng không? | |
| Mức chấm | |
| Ghi chú | |

## Tổng kết vòng test

| Mục | Giá trị |
|-----|---------|
| Số test PASS | |
| Số test WARN | |
| Số test FAIL | |
| Blocker chính | |
| Cần sửa file nào | |
| Có sẵn sàng dùng trong host thật chưa? | |
| Lane/model policy có route nhất quán chưa? | |

## Hành động tiếp theo

- [ ] Không cần sửa gì thêm
- [ ] Chỉ cần chỉnh wording nhẹ
- [ ] Cần sửa routing/trigger
- [ ] Cần sửa session/memory behavior
- [ ] Cần sửa evidence/verification behavior
