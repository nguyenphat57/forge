# Forge Preferences Contract

Use this file when you need the canonical Forge preference schema or when `write_preferences.py` is unavailable and you must edit JSON manually.

## Canonical Fields

Forge stores preferences as one flat JSON object.

| Field | Values | Default | Purpose |
|---|---|---|---|
| `technical_level` | `newbie`, `basic`, `technical` | `basic` | How much jargon Forge should assume |
| `detail_level` | `concise`, `balanced`, `detailed` | `balanced` | Response depth |
| `autonomy_level` | `guided`, `balanced`, `autonomous` | `balanced` | How proactively Forge moves work forward |
| `pace` | `steady`, `balanced`, `fast` | `balanced` | Working speed |
| `feedback_style` | `gentle`, `balanced`, `direct` | `balanced` | How plainly Forge surfaces gaps |
| `personality` | `default`, `mentor`, `strict-coach` | `default` | Coaching style |
| `language` | free-form string | unset | Output language hint |
| `orthography` | free-form string | unset | Orthography hint |
| `tone_detail` | free-form string | unset | Honorific or tone hint |
| `output_quality` | free-form string | unset | Quality target |
| `custom_rules` | array of strings | unset | Extra writing or execution rules |
| `delegation_preference` | `off`, `auto`, `review-lanes`, `parallel-workers` | `auto` | Delegation mode on compatible hosts |

## Persistence Files

- Host-wide defaults: `state/preferences.json`
- Workspace overrides: `.brain/preferences.json`

Both files use the same flat canonical schema.

## Scope Rules

- `global`: update only the host-wide file
- `workspace`: update only the repo-local file
- `both`: write the selected fields to both scopes

Workspace overrides should stay sparse. Only persist repo-specific differences.

## Resolution Rules

1. Start from schema defaults.
2. Overlay host-wide `state/preferences.json` if it exists.
3. Overlay workspace `.brain/preferences.json` if a workspace is in play.
4. Derive output behavior from the merged result.

## Safe Edit Rules

- Do not invent new keys.
- Do not convert the object into nested sections.
- Do not drop unrelated keys when updating one field.
- Keep JSON valid and UTF-8 encoded.
- Prefer the bundled scripts whenever they exist.

## Minimal Examples

### Concise, faster, more direct

```json
{
  "detail_level": "concise",
  "pace": "fast",
  "feedback_style": "direct"
}
```

### Vietnamese with explicit orthography

```json
{
  "language": "vi",
  "orthography": "vietnamese_diacritics"
}
```

### Repo-local tone override

```json
{
  "tone_detail": "Address the user as release manager.",
  "custom_rules": [
    "Keep status updates short and operational."
  ]
}
```
