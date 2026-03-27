# Forge Antigravity — Audit Sau Refactor `common.py`

> **Ngày**: 2026-03-27  
> **Scope**: `packages/forge-core` source + runtime bundle `~/.gemini/antigravity/skills/forge-antigravity/`  
> **Version**: 0.9.0 (HEAD: `ec6028b`)  
> **forge-core tests**: 68 passed, 0 failed, 81 subtests ✅  
> **Runtime bundle tests**: 62 passed, 3 failed ❌ (chưa rebuild)

---

## 1. Tóm tắt

Codex đã tách `common.py` monolith (44KB, 1254 dòng) thành 6 module chuyên biệt + 1 re-export facade. Refactor chất lượng tốt: dependency graph acyclic, backward compatible 100%, tests tăng từ 62 → 68 và pass toàn bộ. Tuy nhiên code **chưa commit** và runtime bundle **chưa rebuild**.

---

## 2. Cấu trúc module mới

| Module | Dòng | Trách nhiệm |
|--------|------|-------------|
| `text_utils.py` | 68 | Normalize, slugify, excerpt, configure_stdio — leaf module |
| `style_maps.py` | 126 | 6 style dicts + `resolve_response_style()` — leaf module |
| `skill_routing.py` | 133 | Token aliases, registry, skill extraction, detect runtimes |
| `error_translation.py` | 162 | Error patterns, sanitize, translate |
| `compat.py` | 445 | Compat detection, translate, serialize, nested value helpers |
| `preferences.py` | 548 | Load/write/normalize preferences, path resolution, migration |
| `common.py` | 93 | Re-export facade — giữ backward compat cho 24 scripts |

### Dependency graph

```
text_utils (leaf)
  ├─→ compat
  ├─→ skill_routing
  ├─→ error_translation
  └─→ preferences (+ compat, style_maps)
        └─→ common (facade, re-export all)
```

--- 

## 3. Findings

### 🔴 Cao

#### F1. Code chưa commit

8 modified + 8 untracked files:

- **New**: `compat.py`, `preferences.py`, `error_translation.py`, `skill_routing.py`, `style_maps.py`, `text_utils.py`, `workflows/operator/customize.md`, `docs/plans/2026-03-26-preferences-simplification-plan.md`
- **Modified**: `common.py`, `write_preferences.py`, `test_preferences.py`, `test_write_preferences.py`, `personalization.md`, 2 customize workflows (antigravity + codex), `test_install_bundle_antigravity_host.py`

#### F2. Runtime bundle chưa rebuild

Runtime tại `~/.gemini/antigravity/skills/forge-antigravity/` vẫn giữ `common.py` monolith 44KB cũ. 3 tests fail do hardcoded path. Cần `build_release.py` + `install_bundle.py`.

#### F3. SKILL.md tree listing thiếu 6 module mới

Cả core lẫn overlay `SKILL.md` liệt kê `scripts/` nhưng thiếu hoàn toàn 6 file mới (`compat.py`, `preferences.py`, `error_translation.py`, `skill_routing.py`, `style_maps.py`, `text_utils.py`). Agent đọc SKILL.md sẽ không biết chúng tồn tại.

---

### 🟡 Trung bình

#### F4. SKILL.md tree indentation lỗi

Cả core (dòng 115-130) lẫn overlay (dòng 119-139) có bug:

```text
# Lỗi hiện tại:
    ├── execution/
        ├── build.md       ← thiếu │ connector
    └── operator/          ← indent sai

# Đúng phải là:
    ├── execution/
    │   ├── build.md
    │   └── test.md
    └── operator/
        ├── bump.md
```

#### F5. Mixed line endings `write_preferences.py`

File có CRLF ở phần cũ và LF ở phần Codex thêm mới. Cần normalize toàn bộ file về cùng một standard.

#### F6. CHANGELOG 0.9.0 placeholder

```markdown
## 0.9.0 - 2026-03-26
- Describe release changes.
```

Chưa viết nội dung thực tế.

#### F7. `ROOT_DIR` khai báo lặp

`ROOT_DIR = Path(__file__).resolve().parent.parent` xuất hiện ở 5 scripts:
- `compat.py`, `preferences.py`, `skill_routing.py` (cùng package, nên single-source)
- `run_smoke_matrix.py`, `verify_bundle.py` (standalone, chấp nhận được)

#### F8. `preferences-compat.json` data duplication

`read.canonical_fields` và `write.canonical_fields` gần giống hệt (~130 dòng duplicate). `compat.py` đã thêm `compat_serialization_fields()` để fallback read → write khi write thiếu, chuẩn bị cho Phase 4 cleanup.

---

### 🟢 Thấp

#### F9. Plan Phase 3-4 chưa thực hiện

| Phase | Mô tả | Trạng thái |
|-------|--------|-----------|
| 0 | Khóa contract + invariant tests | ✅ |
| 1 | Extract modules | ✅ |
| 2 | Split-file extra_preferences.json | ✅ |
| 3 | Write-time migration | ⬜ |
| 4 | Compat write cleanup | ⬜ |
| 5 | Docs/fixtures/workflows | 🔄 |

#### F10. `customize.md` mới chưa trong SKILL.md

`packages/forge-core/workflows/operator/customize.md` (2.8KB, untracked) chưa được liệt kê trong core SKILL.md tree listing và Skill Registry table.

---

## 4. Tổng kết

| Mức | Count | IDs |
|-----|-------|-----|
| 🔴 Cao | 3 | F1, F2, F3 |
| 🟡 Trung bình | 5 | F4, F5, F6, F7, F8 |
| 🟢 Thấp | 2 | F9, F10 |

---

## 5. Đề xuất thứ tự fix

1. **F3 + F4 + F10**: Cập nhật SKILL.md tree (thêm 6 module + fix indent + thêm `customize`)
2. **F5**: Normalize line endings `write_preferences.py`
3. **F6**: Viết CHANGELOG 0.9.0 thực tế
4. **F1**: Commit toàn bộ refactor
5. **F2**: Rebuild + reinstall runtime bundle
6. **F7**: Consolidate `ROOT_DIR` (optional)
7. **F8 + F9**: Tiếp tục plan Phase 3-4 khi sẵn sàng
