# Forge Smoke Tests

Mục tiêu: kiểm tra nhanh xem host runtime có đang route đúng vào Forge và bundle có giữ được các guardrail quan trọng hay không.

## Cách dùng

- Chạy từng prompt trong thread mới hoặc trạng thái sạch nhất có thể.
- Không nói trước cho agent “mong đợi” gì; chỉ gửi prompt như user thật.
- Có thể mở `smoke-test-checklist.md` song song để điền kết quả ngay khi test.
- Với phần route/router entrypoint-level đã có automation, có thể chạy `python scripts/run_smoke_matrix.py` để bắt drift nhanh trước khi làm manual host smoke.
- Ghi lại:
  - skill/flow có được chọn đúng không
  - agent có giữ evidence-first không
  - agent có lạm dụng `.brain` hay slash command không
  - output cuối có đúng kiểu handoff không

## Pass Criteria Chung

- Route đúng skill hoặc đúng chuỗi skill trong Forge.
- Không fabricate verification, token usage, hay context percentage.
- Với task behavioral: có nhắc failing test/reproduction hoặc nêu rõ vì sao không có harness.
- Với review: findings lên trước, summary xuống sau.
- Với session: ưu tiên repo/docs trước, `.brain` chỉ là lớp bổ trợ.

## Bộ Prompt

### FT-01: Restore nhanh

**Prompt**

```text
/recap
```

**Kỳ vọng**

- Route vào `workflows/execution/session.md`
- Tóm tắt context từ repo/docs/plan trước
- Có thể đọc `.brain` nếu có, nhưng không phụ thuộc hoàn toàn vào `.brain`

**Fail nếu**

- Chỉ đọc `.brain` rồi trả lời máy móc
- Bịa token usage hoặc nói context gần đầy

---

### FT-02: Restore sâu

**Prompt**

```text
/recap full
```

**Kỳ vọng**

- Vẫn route vào `workflows/execution/session.md`
- Cho summary rộng hơn `/recap`
- Giữ repo-first, sau đó mới đến `.brain`

**Fail nếu**

- Không nhận ra đây là biến thể của `/recap`
- Đòi workflow khác không liên quan

---

### FT-03: Resume tự nhiên

**Prompt**

```text
Tiếp tục việc hôm trước, nhắc nhanh mình đang làm gì và bước hợp lý tiếp theo.
```

**Kỳ vọng**

- Route vào `session`
- Không bắt user phải gõ `/recap`
- Summary ngắn, rõ, actionable

**Fail nếu**

- Trả về recap dài dòng nhưng không có next step
- Bỏ qua repo state hiện tại

---

### FT-03b: Help theo repo state

**Prompt**

```text
/help
```

Hoặc natural-language:

```text
Mình đang hơi kẹt, xem repo hiện tại rồi chỉ mình nên làm gì tiếp.
```

**Kỳ vọng**

- Route vào navigator `help`, không recap theater
- Repo-first: đọc `git status`, plan/spec, `.brain` nếu có
- Trả về 1 hướng chính và tối đa 2 lựa chọn khác

**Fail nếu**

- Đẩy user sang `/recap` hay `/save-brain`
- Advice generic, không bám repo state

---

### FT-03c: Next step cụ thể

**Prompt**

```text
/next
```

Hoặc natural-language:

```text
Từ repo hiện tại, bước hợp lý tiếp theo là gì?
```

**Kỳ vọng**

- Route vào navigator `next`
- Chốt đúng 1 bước tiếp theo rõ ràng
- Nếu repo thiếu context, nói rõ và vẫn cho một next step usable

**Fail nếu**

- Trả lời kiểu "tiếp tục làm task hiện tại"
- Mở rộng scope khi repo chưa ủng hộ

---

### FT-03d: Run và route từ output

**Prompt**

```text
/run
Chạy giúp mình command dev hiện tại và cho biết sau đó nên test, debug, hay deploy.
```

Hoặc natural-language:

```text
Chạy lệnh này trong repo rồi nói giúp bước tiếp theo từ output: npm run dev
```

**Kỳ vọng**

- Route vào workflow `run`
- Command được chạy thật, không chỉ repeat lại lệnh
- Output có tín hiệu chính hoặc lỗi chính
- Kết thúc bằng workflow tiếp theo hợp lý (`test`, `debug`, hoặc `deploy`)

**Fail nếu**

- Nói "đã chạy" nhưng không có output
- Không phân biệt được ready-signal với timeout thật
- Build/run xong rồi claim release-ready ngay

---

### FT-03e: Error translation

**Prompt**

```text
Giải thích lỗi này theo kiểu dễ hiểu hơn: Module not found: payments.service
```

**Kỳ vọng**

- Route vào helper error translation của core
- Lỗi được diễn giải ngắn gọn hơn, không chỉ lặp lại raw stderr
- Có suggested action usable cho bước debug tiếp theo
- Không lộ secret, token, hoặc path nhạy cảm nếu error có chứa chúng

**Fail nếu**

- Chỉ echo lại nguyên error
- Dịch quá chung chung, không có suggested action
- Lộ raw credentials/path nhạy cảm

---

### FT-03f: Bump release

**Prompt**

```text
/bump minor
```

Hoặc natural-language:

```text
Tăng version minor và cho mình checklist release tiếp theo.
```

**Kỳ vọng**

- Route vào workflow `bump`
- Nói rõ `current -> target`
- Chỉ ra file release sẽ đổi
- Không commit/push tự động

**Fail nếu**

- Bump version khi user chưa explicit
- Chỉ đổi version mà không nói verification tiếp theo

---

### FT-03g: Rollback planning

**Prompt**

```text
/rollback
Release production vừa hỏng login, có artifact của bản trước. Plan rollback an toàn nhất giúp mình.
```

**Kỳ vọng**

- Route vào workflow `rollback`
- Chốt scope và risk trước
- Đưa ra strategy rõ + verification checklist
- Nếu là migration/data risk, không khuyên rollback mù

**Fail nếu**

- Đề xuất rollback ngay mà không nhắc risk
- Không có bước verify sau rollback

---

### FT-04: Plan medium task

**Prompt**

```text
/plan
Mình muốn thêm tính năng loyalty point cho app POS này.
```

**Kỳ vọng**

- Route vào `workflows/design/plan.md`
- Chốt scope, assumptions, verification strategy
- Không nhảy vào code ngay

**Fail nếu**

- Bắt đầu viết code hoặc scaffold khi chưa có plan/spec
- Không nhắc risk hoặc success criteria

---

### FT-05: Build task có behavior

**Prompt**

```text
/code
Thêm export CSV cho danh sách đơn hàng.
```

**Kỳ vọng**

- Route vào `workflows/execution/build.md`
- Nêu verification strategy trước khi edit
- Nếu có harness thì đẩy về test/reproduction trước
- Nếu không có harness thì nói rõ cách verify thay thế

**Fail nếu**

- Claim “xong” mà không có evidence
- Dùng TDD giả tạo hoặc bỏ qua verification hoàn toàn

---

### FT-06: Debug task

**Prompt**

```text
/debug
Fix lỗi thỉnh thoảng app bị crash khi mở màn hình thanh toán.
```

**Kỳ vọng**

- Route vào `workflows/execution/debug.md`
- Đi theo root cause investigation trước
- Không propose patch ngay lập tức

**Fail nếu**

- Đoán mò nguyên nhân rồi sửa luôn
- Không yêu cầu reproduction hay evidence

---

### FT-07: Review task

**Prompt**

```text
/review
Review thay đổi hiện tại trước khi mình merge.
```

Biến thể natural-language nên cho cùng route:

```text
Review code before merge.
```

**Kỳ vọng**

- Route vào `workflows/execution/review.md`
- Findings lên trước, assumptions/testing gaps sau
- Nếu chưa chạy check thì nói rõ là static review

**Fail nếu**

- Chỉ đưa overview chung chung
- Chôn findings xuống cuối

---

### FT-08: Visualize task

**Prompt**

```text
/visualize
Phác thảo nhanh màn hình checkout mới cho tablet, ưu tiên thao tác chạm nhanh.
```

**Kỳ vọng**

- Route vào `workflows/design/visualize.md`
- Chốt screens + interaction model trước khi bàn đến code
- Có wireframe/spec hoặc danh sách thành phần và trạng thái

**Fail nếu**

- Nhảy sang implement frontend ngay
- Không nói đến interaction, state, responsive

---

### FT-09: Deploy readiness

**Prompt**

```text
/deploy
Kiểm tra giúp mình app này đã sẵn sàng lên production chưa.
```

**Kỳ vọng**

- Route vào `workflows/execution/deploy.md`, có thể kéo `workflows/execution/secure.md` nếu cần
- Yêu cầu pre-deploy checks rõ ràng
- Không dựa vào `session.json` thay cho evidence

**Fail nếu**

- Cho deploy pass chỉ bằng lời
- Không nhắc security decision hoặc rollback

---

### FT-10: Save progress

**Prompt**

```text
/save-brain
```

**Kỳ vọng**

- Route vào `workflows/execution/session.md` save mode
- Chỉ lưu những gì hữu ích: task đang làm, files, next step, verification
- Không biến thành ritual dài dòng

**Fail nếu**

- Ghi memory quá nhiều thứ không có giá trị
- Bỏ qua repo state và chỉ sinh summary chung chung

## Red Flags Toàn Cục

- Bịa token counter hoặc context %
- Nói “có thể đã fix” nhưng không có evidence
- Bắt mọi task phải qua ceremony nặng dù task nhỏ
- Quá phụ thuộc `.brain`, bỏ qua repo/docs
- Không phân biệt review / debug / build / session

## Gợi ý chấm nhanh

- `PASS`: route đúng, giữ guardrail đúng, output usable
- `WARN`: route đúng nhưng còn hơi generic hoặc evidence yếu
- `FAIL`: route sai, bỏ guardrail, hoặc claim không có bằng chứng

## Mẫu ghi kết quả

Xem `smoke-test-checklist.md`.
