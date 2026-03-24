---
name: customize
type: flexible
triggers:
  - natural-language request to change tone, detail, autonomy, pace, or feedback style
  - optional alias: /customize
quality_gates:
  - Current preferences are inspected first
  - Durable changes use the core canonical schema and writer
  - The response states what changed and how interaction will feel different
---

# Customize - Codex Preference Wrapper

> Muc tieu: cho Codex mot customize flow ngan, doi style phan hoi ma khong them host-local schema.

## Process

1. Doc preferences hien tai:

```powershell
python scripts/resolve_preferences.py --workspace <workspace> --format json
```

2. Map nhu cau vao cac field canonical:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. Preview hoac persist bang core writer:

```powershell
python scripts/write_preferences.py --workspace <workspace> --detail-level concise --pace fast --feedback-style direct
python scripts/write_preferences.py --workspace <workspace> --detail-level concise --pace fast --feedback-style direct --apply
```

4. Tra loi ngan:
   - field nao da doi
   - style moi se khac nhu the nao

## Activation Announcement

```text
Forge Codex: customize | update canonical preferences with minimal ceremony
```
