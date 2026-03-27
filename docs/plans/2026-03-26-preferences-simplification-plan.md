# Preferences System Deep Refactor Plan

> **Ngày**: 2026-03-26  
> **Phạm vi**: hệ thống preferences, `customize`, compat layer, và module boundaries trong `forge-core`  
> **Mục tiêu**: giảm độ phức tạp của persistence/preferences flow mà vẫn giữ backward compatibility cho hành vi đang public

---

## 1. Tóm tắt

Refactor này vẫn đáng làm, nhưng rollout phải an toàn hơn so với draft trước:

- Tách logic preferences ra khỏi `common.py`
- Giảm phần compat chỉ còn phục vụ legacy migration
- Chuẩn hóa persistence để canonical fields và extras không còn bị trộn logic với nhau
- Giữ nguyên contract bên ngoài trong đợt refactor đầu, đặc biệt là:
  - `resolve_preferences.py --preferences-file` phải là read-only
  - `.brain/preferences.json` vẫn là legacy canonical fallback khi chưa có adapter-global state
  - `output_contract` vẫn phải được trả về

Refactor này không nên giả định rằng mọi adapter mặc định đang ghi đè lên cùng một state file. Installed adapters hiện dùng adapter-global state riêng theo host; xung đột chỉ thực sự xảy ra khi:

- nhiều runtime cùng trỏ vào một `FORGE_HOME` chung, hoặc
- một state file legacy còn ở native format nhưng writer mới lại ghi canonical format vào cùng chỗ đó

Vì vậy, bài toán gốc cần giải là:

1. persistence shape hiện tại khiến compat write path quá phức tạp
2. ownership giữa canonical fields và extras chưa rõ
3. `common.py` đang gom quá nhiều concern

---

## 2. Hiện trạng

### 2.1 State hiện tại

Current adapter-global state vẫn đang dùng một file:

```text
<adapter-home>/state/preferences.json
```

File này có thể ở một trong hai dạng:

- canonical flat format
- host-native/compat format, tùy adapter

Điều này làm writer phải xử lý quá nhiều trường hợp:

- canonical in -> canonical out
- canonical in -> native out
- extras flat -> native nested paths
- preserve existing payload shape nếu file hiện tại là native

### 2.2 Compat layer đang gánh cả read lẫn write

Trong implementation hiện tại:

- compat đọc native -> canonical
- compat trích extras
- compat ghi canonical/extras quay lại native

Điểm đau lớn nhất không nằm ở việc “đọc legacy”, mà ở việc “phải tiếp tục ghi legacy shape” cho state file đang hoạt động.

### 2.3 `common.py` đang là god module

`packages/forge-core/scripts/common.py` hiện chứa nhiều concern:

- preferences schema/defaults/normalize/load/write
- compat helpers
- response style maps
- error translation
- text utils
- skill routing

Điều này làm blast radius của mỗi thay đổi quá lớn.

### 2.4 Contract đang public cần được giữ

Các behavior sau đã có test bám trực tiếp và không nên đổi trong đợt refactor đầu:

- `load_preferences()` vẫn trả về `preferences`, `extra`, `output_contract`, `warnings`
- `resolve_preferences.py` vẫn render `output_contract`
- `write_preferences.py` vẫn render `output_contract`
- `.brain/preferences.json` vẫn có thể cung cấp canonical legacy fallback khi không có adapter-global state

---

## 3. Invariants bắt buộc

### 3.1 Read path không có side effect

`resolve_preferences.py` và `load_preferences()` không được:

- tự rename file
- tự ghi file mới
- tự migrate file chỉ vì bị đọc

Đặc biệt:

- `--preferences-file <path>` phải luôn là explicit read-only inspection
- không được rename file explicit thành `.migrated`

Nếu cần migration, migration phải chạy ở:

- write path khi `--apply`, hoặc
- một helper/migration entrypoint riêng

### 3.2 Giữ semantics của workspace legacy

`.brain/preferences.json` phải tiếp tục được support theo đúng behavior hiện tại:

1. Nếu **không có** adapter-global state:
   - file này là **legacy canonical fallback**
   - có thể chứa cả canonical fields lẫn extras
2. Nếu **có** adapter-global state:
   - file này có thể tiếp tục đóng vai trò **workspace-local extras override**

Nói ngắn gọn: không hạ `.brain/preferences.json` thành “extras-only” trong đợt refactor này.

### 3.3 Giữ `output_contract`

`output_contract` hiện là phần của API đang được scripts/tests dùng. Vì vậy:

- không bỏ trong refactor này
- không merge ngầm vào `extra`
- nếu muốn deprecate, phải là follow-up riêng với consumer audit rõ ràng

### 3.4 Compat asset vẫn thuộc adapter

Trong source tree hiện tại:

- `forge-core` không ship `packages/forge-core/data/preferences-compat.json`
- compat asset thực nằm ở `packages/forge-antigravity/overlay/data/preferences-compat.json`

Do đó plan không được ghi nhầm rằng source-of-truth của compat file nằm ở core data directory.

Core chỉ nên:

- support compat loader một cách optional
- hoạt động bình thường khi compat file không tồn tại

---

## 4. Kiến trúc đích

### 4.1 Persistence shape

Persistence shape đích:

```text
<adapter-home>/state/
├── preferences.json
└── extra_preferences.json
```

`preferences.json` chỉ chứa 6 canonical fields:

```json
{
  "technical_level": "basic",
  "detail_level": "detailed",
  "autonomy_level": "guided",
  "pace": "steady",
  "feedback_style": "direct",
  "personality": "default"
}
```

`extra_preferences.json` chỉ chứa extras:

```json
{
  "language": "vi",
  "orthography": "vietnamese_diacritics",
  "tone_detail": "Gọi Sếp, xưng Em",
  "output_quality": "production_ready",
  "custom_rules": [
    "Mỗi file không được vượt quá 300 dòng..."
  ]
}
```

### 4.2 Lý do chọn split-file

Split-file không phải để “chữa lỗi mọi adapter đang đè nhau” mặc định.

Nó có ích vì:

- tách ownership rõ giữa canonical fields và extras
- loại bỏ nhu cầu serialize canonical/extras quay lại native nested state trong steady-state
- giúp writer merge extras theo key mà không đụng canonical file
- giảm lý do tồn tại của compat write path

### 4.3 Steady-state rules

Sau migration:

- canonical read/write chỉ động vào `state/preferences.json`
- extras read/write chỉ động vào `state/extra_preferences.json`
- compat chỉ còn cần cho legacy read/migration

### 4.4 Legacy support trong rollout

Trong giai đoạn chuyển tiếp, resolver phải support:

1. split-file state mới
2. single-file canonical state cũ
3. native compat state cũ
4. workspace legacy `.brain/preferences.json`

Ưu tiên đọc:

1. explicit `--preferences-file` nếu có
2. split-file adapter-global state nếu tồn tại
3. single-file adapter-global state legacy nếu tồn tại
4. workspace legacy `.brain/preferences.json`
5. defaults

---

## 5. Cấu trúc module

Tách `common.py` thành các module nhỏ hơn:

| Module | Nội dung |
|---|---|
| `scripts/preferences.py` | defaults, schema, normalize, load, write, path resolution |
| `scripts/compat.py` | compat detection, translation, legacy migration helpers |
| `scripts/style_maps.py` | style dicts + `resolve_response_style()` |
| `scripts/error_translation.py` | sanitize + translate error |
| `scripts/text_utils.py` | slugify, normalize text, excerpt, timestamp helpers |
| `scripts/skill_routing.py` | token aliases, repo/runtime/skill routing helpers |
| `scripts/common.py` | re-export shim để giữ import compatibility |

Mục tiêu của `common.py` sau refactor:

- không còn là nơi chứa implementation chính
- chỉ còn import/re-export
- giữ backward compatibility cho scripts/tests đang `from common import ...`

---

## 6. Migration strategy

### 6.1 Nguyên tắc migration

Migration phải an toàn và có thể rollback:

- chỉ áp dụng cho adapter-global state managed bởi Forge
- có backup file cũ
- không chạy ngầm khi chỉ đọc explicit file

### 6.2 Hành vi migration đề xuất

Khi writer chuẩn bị persist vào adapter-global state và phát hiện file legacy:

1. đọc file legacy
2. translate canonical + extras trong memory
3. ghi `state/preferences.json`
4. ghi `state/extra_preferences.json`
5. backup file cũ thành:
   - `preferences.json.legacy.bak` nếu trước đó là single-file legacy
6. trả warning/report rõ ràng rằng state đã được migrate

### 6.3 Explicit file inspection

Nếu user chạy:

```powershell
python scripts/resolve_preferences.py --format json --preferences-file <legacy-file>
```

thì command này chỉ:

- đọc
- translate trong memory
- trả report/warning

và **không được** ghi ra file mới, đổi tên file cũ, hay sửa state root.

### 6.4 Workspace legacy

Workspace legacy chưa migrate tự động.

Nó vẫn được support như compatibility layer:

- canonical fallback khi chưa có adapter-global state
- extras override khi đã có adapter-global state

---

## 7. Execution phases

### Phase 0: Khóa contract và path invariants

Mục tiêu:

- chốt behavior trước khi tách code
- tránh refactor xong mới phát hiện plan đang khác semantics hiện tại

Việc cần làm:

- bổ sung test khẳng định `--preferences-file` là read-only
- bổ sung test khẳng định workspace legacy vẫn là canonical fallback khi thiếu global state
- bổ sung test khẳng định `output_contract` vẫn có mặt trong resolve/write reports
- cập nhật plan/docs để ghi đúng ownership của compat asset

### Phase 1: Extract modules, chưa đổi persistence shape

Mục tiêu:

- tách `common.py` thành các module nhỏ
- giữ nguyên behavior read/write hiện tại

Files:

- `packages/forge-core/scripts/preferences.py` `[NEW]`
- `packages/forge-core/scripts/compat.py` `[NEW]`
- `packages/forge-core/scripts/style_maps.py` `[NEW]`
- `packages/forge-core/scripts/error_translation.py` `[NEW]`
- `packages/forge-core/scripts/text_utils.py` `[NEW]`
- `packages/forge-core/scripts/skill_routing.py` `[NEW]`
- `packages/forge-core/scripts/common.py` `[MODIFY]` re-export only

Gate:

- full `forge-core` tests phải pass trước khi đổi persistence layout

### Phase 2: Add split-file support với backward compatibility

Mục tiêu:

- cho resolver/writer hiểu `extra_preferences.json`
- chưa remove legacy single-file support

Files:

- `packages/forge-core/scripts/preferences.py` `[MODIFY]`
- `packages/forge-core/scripts/resolve_preferences.py` `[MODIFY]`
- `packages/forge-core/scripts/write_preferences.py` `[MODIFY]`

Behavior:

- nếu có split-file state thì đọc split-file
- nếu chưa có split-file state thì vẫn đọc legacy single-file
- `output_contract` vẫn được derive từ `extra`

### Phase 3: Write-time migration

Mục tiêu:

- bỏ nhu cầu tiếp tục persist legacy shape trong steady-state

Files:

- `packages/forge-core/scripts/compat.py` `[MODIFY]`
- `packages/forge-core/scripts/write_preferences.py` `[MODIFY]`
- `packages/forge-core/scripts/preferences.py` `[MODIFY]`

Behavior:

- chỉ khi `--apply` vào adapter-global state mới thực hiện migration
- backup file legacy trước khi split
- explicit `--preferences-file` vẫn read-only

### Phase 4: Compat cleanup

Mục tiêu:

- compat trở thành read/migration-only
- bỏ write duplication khỏi compat asset của adapter đang dùng native payload

Files:

- `packages/forge-antigravity/overlay/data/preferences-compat.json` `[MODIFY]`

Kết quả mong muốn:

- bỏ `write.canonical_fields` duplicate
- giữ phần read mapping và extra mapping cần cho legacy translation

Lưu ý:

- không thêm `preferences-compat.json` mới cho Codex nếu Codex vẫn canonical-only

### Phase 5: Workflow, docs, và fixtures

Files:

- `packages/forge-core/references/personalization.md` `[MODIFY]`
- `packages/forge-core/workflows/operator/customize.md` `[NEW]`
- `packages/forge-antigravity/overlay/workflows/operator/customize.md` `[MODIFY]`
- `packages/forge-codex/overlay/workflows/operator/customize.md` `[MODIFY]`
- `packages/forge-core/tests/fixtures/` `[MODIFY]`
- `packages/forge-core/tests/test_preferences.py` `[MODIFY]`
- `packages/forge-core/tests/test_write_preferences.py` `[MODIFY]`
- `packages/forge-core/tests/test_migration.py` `[NEW]`

Lưu ý:

- overlay `customize.md` vẫn được giữ những guardrail host-specific; không gom cứng đến mức làm mất các hard-gate riêng của Antigravity

---

## 8. Verification plan

```powershell
# Full regression
cd packages/forge-core
python -m pytest tests/ -v

# Resolve current adapter-global state
python scripts/resolve_preferences.py --format json

# Explicit file inspection must stay read-only
python scripts/resolve_preferences.py --format json --preferences-file <legacy-file>

# Preview canonical write
python scripts/write_preferences.py --detail-level detailed --pace fast --format json

# Apply write should migrate legacy adapter-global state when needed
python scripts/write_preferences.py --detail-level detailed --pace fast --apply --format json

# Preview extras write
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --format json

# Apply extras write into split-file state
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --apply --format json
```

Additional assertions:

- explicit file read không tạo file mới
- workspace legacy fallback vẫn pass
- `output_contract` vẫn xuất hiện trong JSON/text output
- split-file state và legacy state cho cùng resolved result

---

## 9. Risk assessment

| Risk | Level | Mitigation |
|---|---|---|
| Đọc file mà vô tình mutate state | High | Cấm migration ở read path; thêm test explicit read-only |
| Break semantics của workspace legacy | High | Giữ nguyên fallback behavior; thêm regression test riêng |
| Break scripts import từ `common.py` | Medium | Re-export shim + full script/test regression |
| Compat asset path bị hiểu sai | Medium | Ghi rõ adapter ownership; không thêm core source path giả |
| Dist/source bị lệch khi rollout | Medium | Rebuild dist sau từng phase có code change |
| `output_contract` bị mất khỏi API | Medium | Giữ nguyên trong refactor này; deprecation tách thành follow-up |

---

## 10. Quyết định được chốt trong bản plan này

1. **Không auto-migrate ở read path**.
2. **Workspace `.brain/preferences.json` vẫn giữ canonical fallback semantics hiện tại**.
3. **`output_contract` được giữ nguyên trong refactor này**.
4. **Codex không cần compat file riêng nếu vẫn dùng canonical-only persistence**.
5. **Compat source-of-truth trong source tree vẫn là adapter overlay đang cần native migration, không phải `forge-core/data`**.

---

## 11. Exit criteria

Refactor được xem là hoàn tất khi:

- `common.py` chỉ còn là re-export shim
- adapter-global steady-state dùng split-file persistence
- legacy state vẫn đọc được
- migration chỉ xảy ra ở write/apply path
- workspace legacy behavior cũ vẫn pass
- `output_contract` vẫn còn trong output
- full `packages/forge-core/tests` pass
