---
name: customize
type: flexible
triggers:
  - user wants to change explanation depth, tone, autonomy, pace, or feedback style
  - user asks how to set language, diacritics, or writing conventions
quality_gates:
  - Current preferences are inspected before changing anything
  - Durable changes use the core canonical schema and writer
  - Durable language rules live in adapter-global extras; workspace `.brain/preferences.json` is only for workspace-specific overrides
  - Output states what changed and what response style will feel different
---

# Customize - Antigravity Preference Wrapper

> Goal: keep customization requests clear for Antigravity users while keeping durable changes on the canonical Forge contract.

<HARD-GATE>
- Do not create Antigravity-specific keys in adapter-global state.
- Do not overwrite all preferences if the user only changes a few fields.
- Do not change routing or gate logic; this workflow only changes response style.
- Reading via `resolve_preferences.py` is read-only; do not mutate state to "preview".
- Legacy single-file Antigravity state may be migrated on the write/apply path; after migration, canonical fields and extras are split into separate files.
- Workspace `.brain/preferences.json` is only for legacy fallback or per-repo overrides, not the default destination for durable language rules.
</HARD-GATE>

## Process

Fast path for language requests:

- If the user only asks how to set language, diacritics, or writing conventions:
  - point directly to a durable adapter-global update via `commands/write_preferences.py`
  - only point to workspace `.brain/preferences.json` when the rule should apply to the current repo only
  - reuse the short template in `workflows/operator/references/personalization.md`

1. Read current preferences:

```powershell
python commands/resolve_preferences.py --format json
```

2. Map user intent to canonical fields when the request is about style:
   - `technical_level`
   - `detail_level`
   - `autonomy_level`
   - `pace`
   - `feedback_style`
   - `personality`

3. If the user wants to lock `language`, `orthography`, or host-native writing rules:
   - persist them via adapter-global extras using `commands/write_preferences.py`
   - do not put them in the 6 canonical fields
   - only use `.brain/preferences.json` for per-workspace overrides

4. Preview or persist using the core writer:

```powershell
python commands/write_preferences.py --detail-level detailed --pace fast --feedback-style direct
python commands/write_preferences.py --detail-level detailed --pace fast --feedback-style direct --apply
python commands/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
```

5. Reply concisely:
   - which preference changed
   - how the response style will feel different
   - if there is a workspace-only override, state that it remains separate from adapter-global state
   - if legacy state was migrated, note that canonical fields and extras are now split

## Output Contract

```text
Changed:
- [...]

New style:
- [...]

Workspace override:
- [...]

Impact:
- [...]
```

## Activation Announcement

```text
Forge Antigravity: customize | update canonical preferences, keep workspace overrides explicit
```
