# Review: Unified Canonical Preferences With Scoped Customize Plan

Status: historical

**Tài liệu được đánh giá:** [Unified Canonical Preferences With Scoped Customize Plan.md](file:///c:/Users/Admin/.gemini/forge/docs/plans/Unified%20Canonical%20Preferences%20With%20Scoped%20Customize%20Plan.md)

**Verdict tổng: ✅ Plan đúng hướng, kiến trúc clean — nhưng blast radius lớn hơn state-machine plan đáng kể. Cần slicing strategy rõ trước khi code.**

**Score: 8.5/10**

---

## 1. Chẩn đoán vấn đề — ✅ Chính xác

Hiện trạng đang như plan mô tả — dữ liệu preferences bị split vào 2 file:

**Global:**
```
state/preferences.json      → 6 style fields (technical_level, detail_level, ...)
state/extra_preferences.json → language, orthography, tone_detail, custom_rules, ...
```

**Hệ quả trong code:**
- [preferences_store.py](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_store.py) — hàm `load_preferences()` (dòng 96-193) phải xử lý **4 code paths** riêng biệt: explicit file, global split, global+extra, workspace-legacy
- [write_preferences.py](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/write_preferences.py) — tách `updates` vs `extra_updates` ở API level
- `compat.py` → `compat_paths.py` → `compat_serialize.py` → `compat_translation.py` — **4 files compat** chỉ để bridge split model

Tổng technical debt từ split model: **~6 files, ~1000 dòng code** chỉ để translate giữa 2 format.

Plan đúng khi nói cần gom lại thành 1 flat canonical object.

---

## 2. Schema Unification — ✅ Thiết kế đúng

### Canonical field set (dòng 79)

```
technical_level, detail_level, autonomy_level, pace, feedback_style, personality,
language, orthography, tone_detail, output_quality, custom_rules, delegation_preference
```

Cross-check với code:
- 6 style fields → [preferences_contract.py PREFERENCE_ALIASES](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_contract.py#L12-L82) ✅
- `language`, `orthography`, `tone_detail` → [resolve_output_contract()](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_contract.py#L182-L237) ✅
- `custom_rules` → [resolve_output_contract() dòng 219-223](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_contract.py#L219-L223) ✅
- `delegation_preference` → [resolve_delegation_preference()](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_contract.py#L153-L179) ✅
- `output_quality` → hiện được xử lý ở compat layer ✅

Không thiếu field nào. Không thừa field nào.

### Precedence model (dòng 12)

```
workspace > global > defaults
```

So với code hiện tại:

```python
# preferences_store.py load_preferences() — resolution order hiện tại:
# 1. explicit file (nếu truyền --preferences-file)
# 2. global path (state/preferences.json + extra)
# 3. workspace-legacy (.brain/preferences.json)
# 4. defaults
```

Hiện tại workspace-legacy là **fallback cuối**, không phải override. Plan đảo lại thành `workspace > global` — đây là **behavioral change** nhưng đúng về semantics: workspace-specific nên win.

> [!IMPORTANT]
> **Đảo precedence order** là breaking change lớn nhất trong plan. Bất kỳ workspace nào có cả global preferences VÀ `.brain/preferences.json` sẽ thay đổi behavior. Hiện tại workspace chỉ dùng khi global không tồn tại. Sau plan, workspace luôn win nếu tồn tại.

---

## 3. Scoped Write Semantics — ✅ Đúng, nhưng có 1 edge case

Plan dòng 21-23:
```
--scope global|workspace|both
default: global
both = write the same selected keys to both files
```

> [!NOTE]
> **Edge case chưa spec:** Khi `--scope workspace` và workspace chưa có `.brain/preferences.json`, hệ thống nên:
> - (a) Tạo file mới chỉ chứa keys được chỉ định, hay
> - (b) Tạo file mới merge từ global + keys được chỉ định?
> 
> Option (a) tạo sparse workspace file → khi resolve, các key không có trong workspace sẽ fall back global → đúng semantics.
> Option (b) tạo full copy → workspace trở thành independent, mất sync với global khi global thay đổi.
> 
> Plan dòng 23 hint option (a) ("writes only explicitly selected keys"), nhưng nên explicit spec behavior khi file chưa tồn tại.

---

## 4. Migration Strategy — ✅ Thận trọng, có backup

Plan dòng 28-33:
- Legacy read path: unified > legacy split > legacy workspace ✅
- First `--apply` auto-migrates + backup `.legacy.bak` ✅
- Sau migration, `extra_preferences.json` bị retire ✅

Code hiện tại ĐÃ có migration logic cơ bản — xem [preferences_store.py dòng 299-313](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_store.py#L299-L313):

```python
if legacy_global_state_detected:
    backup_path = path.with_name(path.name + ".legacy.bak")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    migrated_legacy_global_preferences = True
```

Plan mở rộng pattern này, không phát minh lại — tốt.

---

## 5. Blast Radius — ⚠️ Đây là rủi ro chính

Em đã grep `extra_preferences` trong toàn repo:

| Category | Files ảnh hưởng | Details |
|---|---|---|
| Core scripts | 8 files | `preferences_store.py`, `write_preferences.py`, `resolve_preferences.py`, `compat*.py`, `common.py`, `preferences.py` |
| Tests | 7 files | `test_write_preferences.py`, `test_contracts.py`, `preferences_test_*.py`, `test_route_preview.py` |
| Install/build scripts | 4 files | `install_bundle_host.py`, `install_bundle_paths.py`, `build_release.py`, `operator_surface_support.py` |
| Workflows/docs | 8 files | `customize.md`, `session.md`, `personalization.md`, `kernel-tooling.md`, etc. |
| Generated host artifacts | 5 files | `SKILL.md`, `SKILL.delta.md`, `GEMINI.global.md`, `AGENTS.global.md` |
| Overlay packages | 6 files | `forge-codex` + `forge-antigravity` overlays |
| Architecture docs | 2 files | `AGENTS.global.canonical.md`, `GEMINI.global.canonical.md` |
| Other | 4 files | `CHANGELOG.md`, archived plans/specs |
| **Total** | **~44 files** | |

> [!CAUTION]
> **44 files** cần touch trong 1 tranche. So sánh: state-machine plan chỉ ảnh hưởng ~8-10 files. Plan này nên có explicit slicing strategy để tránh big-bang commit.

### Đề xuất slicing:

| Slice | Scope | Deliverable |
|---|---|---|
| **S1: Schema + resolver** | Core internal | Unified `preferences.json` format + `load_preferences()` đọc được cả unified và legacy |
| **S2: Writer + customize** | Core + operator | `write_preferences()` + `--scope` + migration logic |
| **S3: Install/build** | Build tooling | Host artifact generators, install manifests, build scripts |
| **S4: Docs + overlays** | Non-code | Workflows, references, generated artifacts, overlay packages |
| **S5: Cleanup** | Compat removal | Remove `extra_preferences.json` from active paths, prune compat code |

---

## 6. Test Plan — ✅ Tốt, bổ sung 2 cases

Plan test coverage:
- ✅ Resolver: global, workspace, precedence, derived outputs
- ✅ Migration: legacy split, auto-migrate, backup, workspace legacy
- ✅ Writer: global, workspace, both, selective keys
- ✅ Host/install: generated artifacts reference unified paths
- ✅ End-to-end: targeted suites + full `verify_repo.py`

### Thiếu:

| Test case thiếu | Vì sao cần |
|---|---|
| **Workspace file creation from scratch** | `--scope workspace` khi `.brain/` chưa tồn tại — cần verify `mkdir -p` + chỉ ghi selected keys |
| **Concurrent global + workspace conflict** | Global có `language: "en"`, workspace có `language: "vi"` → resolve PHẢI ra `"vi"`, không phải `"en"` (test cho đảo precedence) |

---

## 7. Public Interface Changes — ✅ Clean break, đúng timing

Plan dòng 83:
```
The cut is intentionally breaking at the public JSON payload level:
extra is removed rather than preserved as a long-term compatibility shim.
```

Đây là quyết định đúng. `extra` key trong JSON output hiện chỉ được đọc bởi:
1. Workflow prose (xử lý bằng text, dễ update)
2. Host artifact generators (controlled code, update cùng lúc)
3. Tests (update cùng slice)

Không có external consumer nào — safe to break.

---

## Đánh giá tổng hợp

| Dimension | Score | Note |
|---|---|---|
| Problem diagnosis | 10/10 | Split-file debt chính xác, quantifiable |
| Schema design | 9/10 | Flat canonical đúng; minor — workspace creation semantics chưa explicit |
| Scoped write | 9/10 | `global|workspace|both` clean; edge case file-creation cần spec |
| Migration | 10/10 | Backup + legacy-read + auto-migrate — robust |
| Blast radius awareness | 6/10 | **44 files nhưng plan không có slicing strategy** |
| Test plan | 8/10 | Tốt; thiếu 2 cases cho precedence flip và workspace creation |
| Interface changes | 10/10 | Clean breaking cut, đúng timing |
| **Overall** | **8.5/10** | |

---

## Recommendations

### Trước khi code:

1. **Thêm slicing strategy** (xem S1-S5 ở trên) — bắt buộc với 44-file blast radius
2. **Spec rõ workspace file creation behavior** — sparse (chỉ selected keys) hay full merge?
3. **Thêm 2 test cases** — workspace creation + precedence conflict

### Trong quá trình implement:

4. **Compat removal (S5) nên là slice cuối** — giữ backward compatibility cho đến khi tất cả consumers đã migrate
5. **`resolve_extra_preferences_path()`** và các helpers trong [preferences_paths.py](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/scripts/preferences_paths.py#L129-L137) nên được mark deprecated trước khi xóa
6. **Chạy `verify_repo.py` sau mỗi slice**, không phải chỉ cuối cùng

### Risk matrix:

| Rủi ro | Mức | Mitigation |
|---|---|---|
| Precedence flip gãy workspace có cả 2 files | **Cao** | Test explicit + document behavioral change |
| Big-bang 44-file commit gãy giữa chừng | **Cao** | Slicing strategy S1-S5 |
| Legacy compat code bị xóa quá sớm | Trung bình | Keep compat qua 1 release cycle |
| Install/build scripts miss update | Thấp | `verify_repo.py` catches |
