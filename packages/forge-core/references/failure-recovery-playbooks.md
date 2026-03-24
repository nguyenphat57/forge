# Forge Failure Recovery Playbooks

> Dùng khi chain đã bị kẹt, gate bị block, hoặc deploy/review/session đi vào trạng thái không thể tiếp tục an toàn nếu cứ improvise.

## Debug Stalled

Khi dùng:
- 2-3 hypotheses liên tiếp không confirm
- 3 fix attempts fail
- reproduction không ổn định

Làm ngay:
1. Dừng patching thêm.
2. Ghi lại hypotheses đã loại trừ.
3. Chọn lại lens: `code`, `data`, hoặc `environment`.
4. Nếu boundary/system shape đang mơ hồ, route sang `plan` hoặc `architect`.

Kết quả mong muốn:
- Có hypothesis mới sắc hơn, hoặc
- Có escalation rõ sang `plan`/`architect`

## Quality Gate Blocked

Khi dùng:
- Quality gate ra `blocked`
- Chưa đủ evidence để claim done/release

Làm ngay:
1. Chỉ ra gate đầu tiên bị fail.
2. Liệt kê đúng evidence còn thiếu.
3. Chọn đường ngắn nhất để lấy evidence đó.
4. Nếu claim hiện tại quá lớn, hạ claim thay vì cố lách gate.

Kết quả mong muốn:
- Gate retry với evidence mới, hoặc
- Claim/disposition nhỏ hơn nhưng đúng

## Deploy Failed Or Smoke Failed

Khi dùng:
- Deploy command fail
- Post-deploy smoke fail
- Identity/target check phát hiện nhầm môi trường

Làm ngay:
1. Dừng rollout tiếp.
2. Chốt release id, target, và phạm vi ảnh hưởng.
3. Nếu user-facing flow chính hỏng, kích hoạt rollback path ngay.
4. Thu log/output đúng điểm fail.
5. Route sang `debug` sau khi service được đưa về trạng thái an toàn.

Kết quả mong muốn:
- Service về trạng thái an toàn, rồi mới điều tra sâu

## Review Deadlock

Khi dùng:
- Feedback qua lại nhưng không hội tụ
- Reviewer và implementer đang tranh luận bằng cảm giác

Làm ngay:
1. Gắn từng feedback vào `feedback response matrix`.
2. Tách rõ: technical fact, convention, hay ownership decision.
3. Nếu dispute là factual, lấy evidence.
4. Nếu dispute là policy/convention, chốt owner quyết định.

Kết quả mong muốn:
- Fix, challenge bằng evidence, hoặc clarification question duy nhất

## Continuity Mismatch

Khi dùng:
- `.brain` nói một đằng, repo state nói một nẻo
- Handover cũ không còn đúng với branch/task hiện tại

Làm ngay:
1. Repo state thắng.
2. Bỏ memory không còn khớp scope hiện tại.
3. Capture lại decision/learning đúng bằng artifact mới nếu cần.
4. Không cố “hòa giải” bằng cách trộn cả hai nguồn.

Kết quả mong muốn:
- Context sạch, scope-filtered, và không mang stale assumptions
