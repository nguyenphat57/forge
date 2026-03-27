---
name: customize
type: flexible
triggers:
  - natural-language request to change tone, detail, autonomy, pace, or feedback style
  - natural-language request to lock language, diacritics, or writing conventions
  - optional alias: /customize
quality_gates:
  - Current preferences are inspected first
  - Durable changes use the core canonical schema and writer
  - Durable language rules live in adapter-global extras; workspace `.brain/preferences.json` is only for workspace-specific overrides
  - The response states what changed and how interaction will feel different
---

# Customize - Codex Preference Wrapper

> Goal: give Codex a short customization flow without inventing host-local preference schema.

## Process

Fast path for language requests:

- If the user only asks how to set language, Vietnamese diacritics, or writing conventions:
  - point first to durable adapter-global updates through `scripts/write_preferences.py`
  - only point to workspace `.brain/preferences.json` when they explicitly want repo-scoped overrides
  - reuse the short templates in `references/personalization.md`

1. Read current preferences:

```powershell
python scripts/resolve_preferences.py --format json
```

2. Map the request into canonical fields when it is about tone or delivery style:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. If the user wants durable language, orthography, or host-native writing rules:
   - persist them through adapter-global extras with `scripts/write_preferences.py`
   - keep them out of the six canonical fields
   - use workspace `.brain/preferences.json` only for workspace-only overrides

4. Preview or persist using the core writer:

```powershell
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct --apply
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
```

5. Persistence notes:
   - canonical fields persist in `state/preferences.json`
   - extras persist in `state/extra_preferences.json`
   - explicit `resolve_preferences.py --preferences-file ...` stays read-only
   - legacy single-file adapter-global state may be migrated on `--apply`

6. Short answer:
   - which fields changed
   - how the new response style will feel different
   - whether any workspace-only overrides remain separate from adapter-global state

## Activation Announcement

```text
Forge Codex: customize | update canonical preferences with minimal ceremony
```
