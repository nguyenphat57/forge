# Forge Personalization

> Goal: keep response-style preferences host-neutral in `forge-customize` so adapters add UX wrappers and locale policy without forking preference logic.

## Preference Contract

- Canonical schema: `data/preferences-schema.json`
- Canonical resolver: `commands/resolve_preferences.py`
- Canonical writer: `commands/write_preferences.py`
- Installed adapters default to adapter-global state under `<host-home>/<adapter-name>/state/`
- Canonical preferences persist in `state/preferences.json`
- `$FORGE_HOME` remains the explicit dev/test override root
- Adapters may ship `data/preferences-compat.json` to translate legacy host-native payloads back into the canonical schema without forking core logic
- Adapters may ship `data/output-contracts.json` to expand bundle-local language or orthography policies from generic canonical preference fields
- `output_contract` is derived from canonical preferences and remains part of the public resolver/writer output

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

Steady-state persistence uses one canonical file per scope:

```text
<adapter-home>/state/
`-- preferences.json
```

`state/preferences.json` and workspace `.brain/preferences.json` both use the same flat canonical object. Workspace files stay sparse and only persist selected repo-local overrides.

Legacy split or native state is still readable during rollout, but new durable writes target the unified canonical layout.

## Resolution Order

1. If `--preferences-file` is provided, inspect that file read-only and fail if it does not exist.
2. If adapter-global `state/preferences.json` exists, read it as canonical or legacy native state.
3. If `--workspace` is provided and `.brain/preferences.json` exists, overlay it per key on top of adapter-global state.
4. If no valid file exists, use schema defaults plus any compat defaults.

Important:

- `resolve_preferences.py --preferences-file ...` is read-only inspection. It must not rename, migrate, or rewrite the inspected file.
- Explicit inspection should target the canonical `preferences.json` file. Legacy `extra_preferences.json` remains migration input for the surrounding global state and is not a first-class inspection target.
- Migration belongs on write/apply flows, not read-only inspection.

## Validation Rules

- Invalid JSON or invalid enum values fall back to defaults in non-strict mode and return warnings.
- `--strict` turns those warnings into hard failures.
- Aliases such as `strict_coach`, `beginner`, `verbose`, `low`, `high`, `slow`, `rapid`, `gentle`, and `strict` normalize to canonical enum values.

## Response Style Resolver

The resolver does not create host-specific command surfaces. It returns a response-style contract that the adapter or prompt entry point can apply:

- terminology policy
- explanation policy
- verbosity and context depth
- decision and autonomy policy
- delivery pace
- feedback style
- tone, teaching mode, and challenge level

When canonical preferences contain host-native rules, the resolver also emits `output_contract` for:

- language policy
- orthography policy
- tone detail or honorific hints
- custom writing rules the adapter should preserve

`forge-customize` treats these fields generically. If an adapter needs bundle-specific language behavior, it should encode that in bundle-local `data/output-contracts.json`, not in adapter-specific preference logic.

## Persistence Flow

When an adapter wants to record durable preferences:

```powershell
python commands/write_preferences.py --technical-level newbie --pace fast --feedback-style direct --scope global --apply
python commands/write_preferences.py --language en --orthography plain_english --scope workspace --apply
python commands/write_preferences.py --clear-field language --clear-field orthography --scope workspace --apply
```

Rules:

- The writer merges with existing preferences by default
- `--replace` clears the target scope first, then writes only explicit keys
- Durable adapter-wide language or orthography rules should go through `commands/write_preferences.py`
- Workspace-local overrides may still live in `.brain/preferences.json` when the user explicitly wants repo-specific behavior
- Adapters cannot invent host-local canonical schema or change the meaning of the six canonical fields
- Applying a write may migrate legacy adapter-global split or native state into the unified canonical file

## Workspace Legacy Behavior

Workspace `.brain/preferences.json` is supported as:

- workspace-local override when a repo needs rules different from the adapter-wide default

Existing repos that already rely on canonical fields in `.brain/preferences.json` continue to resolve correctly.

## Writing Templates

Use the writer for adapter-wide durable rules:

```powershell
python commands/write_preferences.py --language en --orthography plain_english --scope global --apply
python commands/write_preferences.py --language en --clear-field orthography --scope workspace --apply
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

- If the user asks how to set language durably, point to `commands/write_preferences.py` first
- Only point to workspace `.brain/preferences.json` when the user explicitly wants workspace-scoped behavior or a repo-specific override
- Only surface grouped display sections for readability; storage stays one flat canonical object

## Adapter Boundary

- Host adapters may ship compat defaults, onboarding wrappers, and bundle-local output-contract profiles without inventing a dedicated `customize` operator
- The active host adapter should keep durable preference changes natural-language first and let adapter-global state drive durable language rules
- Future adapters should be able to reuse this schema with compat mapping and bundle-local output-contract profiles instead of a fork

