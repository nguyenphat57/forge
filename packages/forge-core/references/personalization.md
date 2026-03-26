# Forge Personalization

> Goal: keep response-style preferences host-neutral in `forge-core` so adapters only add UX wrappers, not forked preference logic.

## Core Contract

- Canonical schema: `data/preferences-schema.json`
- Canonical resolver: `scripts/resolve_preferences.py`
- Canonical writer: `scripts/write_preferences.py`
- Installed adapters default to adapter-global state at `<host-home>/<adapter-name>/state/preferences.json`
- `$FORGE_HOME/state/preferences.json` is an explicit dev/test override; when no installed adapter metadata or override exists, core falls back to `~/.forge/state/preferences.json`
- Adapters may ship `data/preferences-compat.json` to map host-native payloads back to the canonical schema without forking the core engine
- Host-native extra preferences such as `language`, `orthography`, `tone_detail`, `output_quality`, or `custom_rules` can live in adapter-global state and are returned through `extra`
- Workspace `.brain/preferences.json` is still supported as:
  - legacy canonical fallback when no adapter-global state exists
  - workspace-local extra override when a repo needs rules different from the adapter-wide default
- Core can infer `output_contract` from `extra` for language, orthography, tone detail, and custom writing rules
- Adapters may add `customize` UX, but they cannot change the meaning of the canonical keys

## Supported Fields

| Field | Values | Default | Purpose |
|------|--------|---------|---------|
| `technical_level` | `newbie`, `basic`, `technical` | `basic` | Adjust terminology and explanation level |
| `detail_level` | `concise`, `balanced`, `detailed` | `balanced` | Adjust response depth and length |
| `autonomy_level` | `guided`, `balanced`, `autonomous` | `balanced` | Adjust how proactively Forge moves the task forward |
| `pace` | `steady`, `balanced`, `fast` | `balanced` | Adjust delivery pace |
| `feedback_style` | `gentle`, `balanced`, `direct` | `balanced` | Adjust how plainly gaps are called out |
| `personality` | `default`, `mentor`, `strict-coach` | `default` | Adjust coaching tone |

## Resolution Order

1. If `--preferences-file` is provided, use that file and fail if it does not exist.
2. If valid adapter-global Forge state exists, read the running adapter's `state/preferences.json` and preserve any host-native extras outside the canonical schema.
3. If there is no adapter-global file and `--workspace` is provided, read legacy `.brain/preferences.json` in that workspace for canonical fallback. That same file may also provide workspace-local extra overrides.
4. If no valid file exists, use schema defaults plus any adapter compat defaults.

## Validation Rules

- Invalid JSON or invalid enum values fall back to defaults in non-strict mode and return warnings.
- `--strict` turns those warnings into hard failures.
- Aliases such as `strict_coach`, `beginner`, `verbose`, `low`, `high`, `slow`, `rapid`, `gentle`, and `strict` normalize to canonical enum values.

## Response Style Resolver

The resolver does not create host-specific command surfaces. It returns a response-style contract that the adapter or prompt entrypoint can apply:

- terminology policy
- explanation policy
- verbosity and context depth
- decision and autonomy policy
- delivery pace
- feedback style
- tone, teaching mode, and challenge level

When `extra` contains host-native rules, core can also emit `output_contract` for:

- language policy
- orthography or diacritics policy
- tone detail or honorific hints
- custom writing rules the adapter should preserve

## Persistence Flow

When an adapter wants to record durable preferences:

```powershell
python scripts/write_preferences.py --technical-level newbie --pace fast --feedback-style direct --apply
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
python scripts/write_preferences.py --clear-language --clear-orthography --apply
```

Rules:

- The writer merges with existing preferences by default
- `--replace` resets omitted canonical fields to schema defaults
- Durable adapter-wide language or orthography rules should go through `scripts/write_preferences.py`
- Workspace-local overrides may still live in `.brain/preferences.json` when the user explicitly wants repo-specific behavior
- Adapters cannot invent host-local canonical schema or change the meaning of the six canonical fields

## Language And Writing Templates

Use the writer for adapter-wide durable rules:

```powershell
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
python scripts/write_preferences.py --language en --clear-orthography --apply
```

Use workspace `.brain/preferences.json` only when the repo needs local overrides that should not become adapter-wide defaults.

Sample 1: Vietnamese with full diacritics in one workspace

```json
{
  "language": "vi",
  "orthography": "vietnamese_diacritics",
  "custom_rules": [
    "Luôn giao tiếp với user bằng tiếng Việt có dấu.",
    "Không dùng tiếng Việt không dấu trong comment, summary, plan, review, hay text giải thích."
  ]
}
```

Sample 2: English in one workspace

```json
{
  "language": "en",
  "custom_rules": [
    "Always communicate with the user in English."
  ]
}
```

Sample 3: Explain in Vietnamese, keep code and comments in English

```json
{
  "language": "vi",
  "custom_rules": [
    "Giải thích cho user bằng tiếng Việt có dấu.",
    "Giữ code identifiers, commit messages, và code comments bằng tiếng Anh khi phù hợp với repo."
  ]
}
```

Operator rule:

- If the user asks how to set language durably, point to `scripts/write_preferences.py` first
- Only point to workspace `.brain/preferences.json` when the user explicitly wants workspace-scoped behavior or a repo-specific override
- Only surface the six canonical fields when the user is changing tone, detail, autonomy, pace, feedback, or personality

## Adapter Boundary

- `forge-antigravity`: may add `/customize` or onboarding wrappers, and may ship compat defaults such as `language=vi`, but still writes through the core writer
- `forge-codex`: should keep a natural-language customize flow and let adapter-global state drive durable language rules
- Future adapters such as `forge-claude` should be able to reuse this schema with compat mapping instead of a fork
