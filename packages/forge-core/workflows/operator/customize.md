---
name: customize
type: flexible
triggers:
  - user wants to change explanation depth, tone, autonomy, pace, or feedback style
  - user asks how to set language, diacritics, or writing conventions
quality_gates:
  - Current preferences are inspected before changing anything
  - Durable changes use the canonical core schema and writer
  - Workspace `.brain/preferences.json` is only for legacy fallback or workspace-local overrides
  - Read-only inspection does not mutate state files
  - The response states what changed and how interaction will feel different
---

# Customize - Core Preference Flow

> Goal: update durable Forge preferences without inventing adapter-local canonical schema or mutating state during inspection.

<HARD-GATE>
- Do not invent new canonical preference keys.
- Do not overwrite the whole preference state when the user only changes one or two fields.
- Do not mutate state during `resolve_preferences.py` inspection.
- Keep `output_contract` intact in resolver/writer output.
- Preserve workspace `.brain/preferences.json` as legacy fallback or workspace-only override, not as the default durable state.
</HARD-GATE>

## Process

1. Read current preferences first:

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

3. If the user wants durable language, orthography, or adapter-global writing rules:
   - persist them through `scripts/write_preferences.py`
   - keep them in adapter-global extras, not in the six canonical fields
   - let adapters expand locale-specific output policy through bundle-local data instead of core-specific branching
   - use workspace `.brain/preferences.json` only when the user explicitly wants repo-scoped behavior

4. Preview or persist with the writer:

```powershell
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct
python scripts/write_preferences.py --detail-level concise --pace fast --feedback-style direct --apply
python scripts/write_preferences.py --language en --orthography plain_english --apply
```

5. Persistence notes:
   - canonical values live in `state/preferences.json`
   - extras live in `state/extra_preferences.json`
   - legacy single-file state may be migrated on `--apply`
   - explicit `--preferences-file` inspection stays read-only

6. Reply briefly with:
   - which fields changed
   - how the new response style will feel different
   - whether any workspace-only overrides remain separate from adapter-global state

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
Forge: customize | update canonical preferences, keep read-only inspection side-effect free
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: customize`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.