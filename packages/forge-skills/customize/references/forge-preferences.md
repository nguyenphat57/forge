# Forge Preferences

Canonical Forge preferences use a flat JSON object.

Supported fields:

- `technical_level`
- `detail_level`
- `autonomy_level`
- `pace`
- `feedback_style`
- `personality`
- `language`
- `orthography`
- `tone_detail`
- `output_quality`
- `custom_rules`

Scope rules:

- `global` writes adapter-wide defaults into `state/preferences.json`
- `workspace` writes repo-local overrides into `.brain/preferences.json`
- `both` writes the same explicit field values into both scopes

Rules:

- Preserve unrelated keys.
- Keep UTF-8 encoding.
- Use sparse workspace overrides instead of duplicating global state.
- Prefer `--clear-field` for removing one override without rewriting the object.
