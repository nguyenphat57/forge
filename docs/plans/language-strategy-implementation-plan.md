# Forge Language Strategy: Implementation Plan

## Mục tiêu

Triển khai quyết định:

- `forge-core` và `forge-codex` mặc định tiếng Anh
- `forge-antigravity` giữ tiếng Việt cho user-facing output
- ngôn ngữ output đi qua preference + output contract

## Nguyên tắc thực hiện

1. Không dịch prose hàng loạt trước khi khóa `language` contract.
2. Không overlay dày cho `forge-antigravity` từ đầu.
3. Không đẩy toàn bộ multilingual routing xuống từng adapter nếu data layer xử lý được.
4. Mỗi phase phải có tiêu chí xong việc và kiểm chứng rõ ràng.

## Phase 0: Language Contract

### Mục tiêu

Làm cho `language` và `orthography` có đường đi rõ ràng từ cấu hình đến output behavior.

### Việc cần làm

- rà `preferences-schema`, `common.py`, `resolve_preferences.py`, `write_preferences.py`
- rà compat payload của `forge-antigravity`
- quyết định `language` và `orthography` là:
  - extra fields được hỗ trợ chính thức
  - hay canonical fields mới
- thêm đường ghi rõ ràng cho `language` / `orthography`
- chuẩn hóa merge rule giữa:
  - global preferences
  - workspace legacy preferences
  - compat payload
  - workspace extra preferences

### Deliverables

- contract rõ cho `language` / `orthography`
- implementation đọc/ghi tương thích
- test round-trip cho EN/VN

### Exit criteria

- có thể đọc `language=vi`
- có thể ghi `language=vi`
- round-trip không mất `orthography`
- Codex default ra `en`
- Antigravity default ra `vi`

## Phase 1: Convert `forge-core` to English

### Mục tiêu

Đưa toàn bộ prose cốt lõi về tiếng Anh mà không làm đổi hành vi router/tooling.

### Việc cần làm

- dịch [SKILL.md](C:/Users/Admin/.gemini/forge/packages/forge-core/SKILL.md)
- dịch `workflows/design/*.md`
- dịch `workflows/execution/*.md`
- dịch `workflows/operator/*.md`
- dịch `references/*.md`
- dịch `domains/*.md`
- giữ `scripts/` và `data/` tiếp tục là tiếng Anh

### Nguyên tắc nội dung

- giữ nguyên semantics, chỉ đổi ngôn ngữ
- không đổi tên skill, file path, contract key
- tránh “dịch văn vẻ”; ưu tiên wording rõ, vận hành được

### Exit criteria

- prose trong core nhất quán EN
- không còn section tiếng Việt lẫn trong core trừ ví dụ có chủ đích
- test hiện có vẫn pass

## Phase 2: Normalize `forge-codex`

### Mục tiêu

Làm `forge-codex` nhất quán với core EN nhưng vẫn giữ khả năng output tiếng Việt khi preference yêu cầu.

### Việc cần làm

- dịch các phần VN còn lại trong [SKILL.md](C:/Users/Admin/.gemini/forge/packages/forge-codex/overlay/SKILL.md)
- rà `AGENTS.global.md` và `AGENTS.example.md`
- rà `dispatch-subagents.md`
- rà operator docs trong overlay
- giữ explicit rule cho `language=vi` và full Vietnamese diacritics

### Exit criteria

- codex overlay prose là EN
- rule output VN vẫn còn rõ
- test preferences / routing / operator docs vẫn pass

## Phase 3: Keep `forge-antigravity` Vietnamese by Design

### Mục tiêu

Giữ trải nghiệm tiếng Việt mà không tạo overlay burden không cần thiết.

### Việc cần làm

- giữ VN ở [SKILL.md](C:/Users/Admin/.gemini/forge/packages/forge-antigravity/overlay/SKILL.md)
- giữ VN ở communication rules, honorific rules, orthography rules
- giữ VN ở operator-facing docs riêng của antigravity
- chỉ overlay workflow bổ sung nếu test thực tế chứng minh EN workflow làm giảm chất lượng đầu ra

### Exit criteria

- antigravity default ra tiếng Việt
- user-facing guidance trong antigravity vẫn rõ và tự nhiên
- overlay scope còn mỏng, không sao chép toàn bộ core không cần thiết

## Phase 4: Routing and Preference Validation

### Mục tiêu

Xác nhận routing và output contract hoạt động đúng cho cả EN và VN.

### Việc cần làm

- smoke test prompt EN
- smoke test prompt VN
- smoke test mixed prompt
- test intent detection cho keyword EN/VN ở data layer
- test output contract cho:
  - `language=en`
  - `language=vi`
  - `orthography=vietnamese-diacritics`

### Exit criteria

- route không bị regress với prompt tiếng Việt
- output contract phản ánh đúng preference
- không có drift rõ giữa Codex và Antigravity

## Phase 5: Bundle Build and Release Verification

### Mục tiêu

Đảm bảo tất cả bundles build được và không vỡ contract sau migration.

### Việc cần làm

- build `forge-core`
- build `forge-codex`
- build `forge-antigravity`
- chạy smoke tests
- chạy verification entrypoint của bundle

### Exit criteria

- build thành công cho cả 3 package
- smoke tests pass
- bundle integrity pass

## Thứ tự thực hiện khuyến nghị

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5

Không đảo thứ tự Phase 0 ra sau.

## Rủi ro chính

### Rủi ro 1: `language` chỉ đọc được nhưng ghi không ổn

Giảm thiểu:

- chốt contract trước
- thêm round-trip tests trước khi dịch prose

### Rủi ro 2: Core EN làm giảm chất lượng đầu ra VN

Giảm thiểu:

- smoke test prompt VN trên antigravity
- chỉ tăng overlay khi có bằng chứng

### Rủi ro 3: Drift giữa core và overlays

Giảm thiểu:

- overlay mỏng
- ưu tiên data/config-driven behavior
- tránh copy cả workflow nếu không cần

## Kết quả mong đợi

Sau khi hoàn tất plan này:

- `forge-core` là English-first source of truth
- `forge-codex` nhất quán với core
- `forge-antigravity` vẫn giữ trải nghiệm tiếng Việt
- `language` behavior được bảo vệ bằng contract và test, không chỉ bằng prose
