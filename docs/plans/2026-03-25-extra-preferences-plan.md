# Plan: Extra Preferences Support

Created: 2026-03-25 | Status: Pending review

## Problem

File `forge-antigravity/state/preferences.json` chứa cả canonical fields (technical_level, autonomy...) lẫn workspace-specific fields (tone_detail, language, output_quality, custom_rules). Adapter `resolve_preferences.py` chỉ trả canonical, bỏ mất phần còn lại.

## Chosen Approach

- Canonical schema giữ nguyên ở global level
- Non-canonical fields tách ra workspace `.brain/preferences.json` dưới dạng `extra`
- Adapter forward cả hai, không conflict

## Data Flow

```
Global file ──→ compat translate ──→ canonical preferences
      │                                      │
      └── extract_extras ──────┐             │
                               ▼             ▼
Workspace .brain/prefs.json ──→ merge ──→ "extra" field in output
```

## File / Surface Map

### 1. Core Adapter

#### [MODIFY] `scripts/common.py`

1. **New function `extract_extras(raw_payload, compat_config)`**:
   - Walk toàn bộ keys trong raw payload
   - Collect key/value không nằm trong canonical mapping paths
   - Giữ nguyên structure gốc, loại bỏ leaf values đã mapped sang canonical
   - Đặc biệt giữ `custom_rules` (top-level array)

2. **Update `load_preferences()`**:
   - Gọi `extract_extras` trên raw payload
   - Thêm `"extra"` vào report dict

#### [MODIFY] `scripts/resolve_preferences.py`

1. Load workspace extras từ `.brain/preferences.json` nếu workspace được chỉ định
2. **Merge**: `extra` = workspace extras (ưu tiên) merged với extras từ global file
3. Thêm `"extra"` vào output payload
4. Format extras trong text output

### 2. Workspace File

#### [NEW] `.brain/preferences.json`

```json
{
  "tone_detail": "Gọi Sếp, xưng Em",
  "language": "vi",
  "output_quality": "production_ready",
  "custom_rules": [
    "Mỗi file không được vượt quá 300 dòng, nếu vượt phải chia nhỏ ra",
    "Mỗi file chỉ chứa một chức năng, không gộp hay chồng chéo chức năng vào 1 file",
    "Luôn dùng TypeScript thay vì JavaScript",
    "Luôn sử dụng PowerShell thay vì Command Prompt",
    "Luôn sử dụng ; thay vì && cho PowerShell",
    "Luôn debug log mỗi hành động, không đoán mò lỗi"
  ]
}
```

### 3. Tests

#### [MODIFY] `tests/test_preferences.py`

Thêm 2 test cases:
- `test_extras_extracted_from_compat_payload`: verify `extract_extras` trả đúng `tone_detail`, `language`, `custom_rules` từ compat payload
- `test_resolve_preferences_includes_workspace_extras`: verify script output có `extra` field khi workspace có `.brain/preferences.json`

## Verification

### Automated

```powershell
cd C:\Users\Admin\.gemini\antigravity\skills\forge-antigravity\tests; python -m pytest test_preferences.py -v
```

Existing 7 tests phải pass (canonical pipeline không bị ảnh hưởng) + 2 tests mới.

### Manual Smoke

```powershell
python scripts/resolve_preferences.py --workspace "c:\Users\Admin\.gemini\LamDiFood" --format json
```

Expected: output có `"extra"` chứa `tone_detail`, `language`, `output_quality`, `custom_rules`.

## Constraints

- Không sửa `preferences-schema.json` — canonical schema giữ nguyên 6 fields
- Không sửa `preferences-compat.json` — compat mapping giữ nguyên
- Global file giữ nguyên — compat layer vẫn translate sang canonical như cũ
- `extra` là additive, không ảnh hưởng `response_style` derivation
