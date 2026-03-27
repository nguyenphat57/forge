# Forge Personalization

> Goal: keep response-style preferences host-neutral in `forge-core` so adapters add UX wrappers and locale policy without forking preference logic.

## Core Contract

- Canonical schema: `data/preferences-schema.json`
- Canonical resolver: `scripts/resolve_preferences.py`
- Canonical writer: `scripts/write_preferences.py`
- Installed adapters default to adapter-global state under `<host-home>/<adapter-name>/state/`
- Canonical fields persist in `state/preferences.json`
- Adapter-global extras persist in `state/extra_preferences.json`
- `$FORGE_HOME` remains the explicit dev/test override root
- Adapters may ship `data/preferences-compat.json` to translate legacy host-native payloads back into the canonical schema without forking core logic
- Adapters may ship `data/output-contracts.json` to expand bundle-local language or orthography policies from generic extra fields
- `output_contract` is still derived from `extra` and remains part of the public resolver/writer output

## Supported Fields

| Field | Values | Default | Purpose |
|---|---|---|---|
| `technical_level` | `newbie`, `basic`, `technical` | `basic` | Adjust terminology and explanation level |
| `detail_level` | `concise`, `balanced`, `detailed` | `balanced` | Adjust response depth and length |
| `autonomy_level` | `guided`, `balanced`, `autonomous` | `balanced` | Adjust how proactively Forge moves the task forward |
| `pace` | `steady`, `balanced`, `fast` | `balanced` | Adjust delivery pace |
| `feedback_style` | `gentle`, `balanced`, `direct` | `balanced` | Adjust how plainly gaps are called out |
| `personality` | `default`, `mentor`, `strict-coach` | `default` | Adjust coaching tone |

## Persistence Layout

Steady-state adapter-global persistence uses two files:

```text
<adapter-home>/state/
|-- preferences.json
`-- extra_preferences.json
```

`preferences.json` contains only the six canonical fields.

`extra_preferences.json` contains adapter-global extras such as:

- `language`
- `orthography`
- `tone_detail`
- `output_quality`
- `custom_rules`

Legacy single-file state is still readable during rollout, but new durable writes target the split-file layout.

## Resolution Order

1. If `--preferences-file` is provided, inspect that file read-only and fail if it does not exist.
2. If adapter-global split-file state exists, read `state/preferences.json` plus sibling `state/extra_preferences.json` when present.
3. If only adapter-global `state/preferences.json` exists, read it as canonical or legacy single-file state.
4. If there is no adapter-global state and `--workspace` is provided, read legacy `.brain/preferences.json` as canonical fallback.
5. When adapter-global state exists, workspace `.brain/preferences.json` may still contribute workspace-local extra overrides.
6. If no valid file exists, use schema defaults plus any compat defaults.

Important:

- `resolve_preferences.py --preferences-file ...` is read-only inspection. It must not rename, migrate, or rewrite the inspected file.
- Migration belongs on write/apply flows, not read-only inspection.

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

When `extra` contains host-native rules, core also emits `output_contract` for:

- language policy
- orthography policy
- tone detail or honorific hints
- custom writing rules the adapter should preserve

`forge-core` treats these fields generically. If an adapter needs bundle-specific language behavior, it should encode that in bundle-local `data/output-contracts.json`, not in core logic.

## Persistence Flow

When an adapter wants to record durable preferences:

```powershell
python scripts/write_preferences.py --technical-level newbie --pace fast --feedback-style direct --apply
python scripts/write_preferences.py --language en --orthography plain_english --apply
python scripts/write_preferences.py --clear-language --clear-orthography --apply
```

Rules:

- The writer merges with existing preferences by default
- `--replace` resets omitted canonical fields to schema defaults
- Durable adapter-wide language or orthography rules should go through `scripts/write_preferences.py`
- Workspace-local overrides may still live in `.brain/preferences.json` when the user explicitly wants repo-specific behavior
- Adapters cannot invent host-local canonical schema or change the meaning of the six canonical fields
- Applying a write may migrate legacy adapter-global single-file state into split canonical + extra files

## Workspace Legacy Behavior

Workspace `.brain/preferences.json` is still supported as:

- legacy canonical fallback when no adapter-global state exists
- workspace-local extra override when a repo needs rules different from the adapter-wide default

This means workspace legacy is not reduced to extras-only. Existing repos that still rely on canonical fields in `.brain/preferences.json` continue to resolve correctly.

## Writing Templates

Use the writer for adapter-wide durable rules:

```powershell
python scripts/write_preferences.py --language en --orthography plain_english --apply
python scripts/write_preferences.py --language en --clear-orthography --apply
```

Use workspace `.brain/preferences.json` only when the repo needs local overrides that should not become adapter-wide defaults.

Sample 1: English workspace default

```json
{
  "language": "en",
  "custom_rules": [
    "Always communicate with the user in English."
  ]
}
```

Sample 2: English with an explicit house style

```json
{
  "language": "en",
  "orthography": "plain_english",
  "custom_rules": [
    "Keep code identifiers, commit messages, and code comments aligned with the repository style guide."
  ]
}
```

Sample 3: Repo-specific tone detail

```json
{
  "tone_detail": "Address the user as release manager.",
  "custom_rules": [
    "Keep status updates short and operational.",
    "State risks before proposing follow-up work."
  ]
}
```

Operator rule:

- If the user asks how to set language durably, point to `scripts/write_preferences.py` first
- Only point to workspace `.brain/preferences.json` when the user explicitly wants workspace-scoped behavior or a repo-specific override
- Only surface the six canonical fields when the user is changing tone, detail, autonomy, pace, feedback, or personality

## Adapter Boundary

- `forge-antigravity`: may add `/customize` or onboarding wrappers, may ship compat defaults, and may ship bundle-local output-contract profiles
- `forge-codex`: should keep a natural-language customize flow and let adapter-global state drive durable language rules
- Future adapters such as `forge-claude` should be able to reuse this schema with compat mapping and bundle-local output-contract profiles instead of a fork
