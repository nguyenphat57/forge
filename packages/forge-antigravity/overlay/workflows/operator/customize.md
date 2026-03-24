---
name: customize
type: flexible
triggers:
  - shortcut: /customize
  - user wants to change explanation depth, tone, autonomy, pace, or feedback style
quality_gates:
  - Current preferences are inspected before changing anything
  - Durable changes use the core canonical schema and writer
  - Output states what changed and what response style will feel different
---

# Customize - Antigravity Preference Wrapper

> Muc tieu: cho user Antigravity mot be mat `/customize` ro rang, nhung van ghi vao schema canonical cua Forge.

<HARD-GATE>
- Khong tao key rieng cho Antigravity.
- Khong overwrite toan bo preferences neu user chi doi mot vai field.
- Khong doi routing/gate logic; workflow nay chi doi response style.
</HARD-GATE>

## Process

1. Doc preferences hien tai:

```powershell
python scripts/resolve_preferences.py --workspace <workspace> --format json
```

2. Map user intent vao cac field canonical:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. Preview hoac persist bang core writer:

```powershell
python scripts/write_preferences.py --workspace <workspace> --detail-level detailed --pace fast --feedback-style direct
python scripts/write_preferences.py --workspace <workspace> --detail-level detailed --pace fast --feedback-style direct --apply
```

4. Tra loi ngan:
   - preferences moi
   - field nao da doi
   - response se khac nhu the nao

## Output Contract

```text
Da doi:
- [...]

Style moi:
- [...]

Tac dong:
- [...]
```

## Activation Announcement

```text
Forge Antigravity: customize | update canonical preferences, not host-local hacks
```
