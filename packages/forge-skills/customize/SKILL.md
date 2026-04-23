---
name: forge-customize
description: Use when the user wants to change host-neutral Forge preferences such as explanation depth, tone, autonomy, pace, feedback style, language, orthography, delegation, or custom writing rules across Forge hosts.
---

# Forge Customize

<EXTREMELY-IMPORTANT>
Inspect current preferences before proposing durable changes.

Do not invent host-local keys, and do not mutate state during read-only inspection.
</EXTREMELY-IMPORTANT>

## Overview

Customize durable Forge response preferences without inventing host-local schema or mutating state during inspection.

**Core principle:** inspect the effective preferences first, then map only the requested changes onto canonical Forge fields and the correct persistence scope.

## When to Use

- The user wants Forge to be shorter, more detailed, faster, slower, gentler, or more direct.
- The user wants durable language, orthography, tone, delegation, or writing-rule changes across Forge hosts.
- The user wants a repo-local override in `.brain/preferences.json` instead of changing the host-wide default.
- The user wants to inspect the current effective Forge preferences before deciding what to change.

When NOT to use:
- Do not use this skill for one-off prompt wording that should not be persisted.
- Do not use this skill when the requested behavior is not representable with canonical Forge preference fields.
- Do not use this skill as a substitute for debugging the preference scripts themselves.

## Quick Reference

| Need | Canonical target | Preferred action |
|---|---|---|
| Inspect effective preferences | read-only merged view | `resolve_preferences.py --format json` |
| Shorter, faster, more direct replies | `detail_level`, `pace`, `feedback_style` | write only the requested fields |
| Repo-only language or orthography | `language`, `orthography` with `workspace` scope | write sparse `.brain/preferences.json` overrides |
| Remove a local override | selected field with `--clear-field` | clear only that field, keep unrelated keys |
| Same change globally and locally | explicit `both` scope | use only when the user asks for both |

## Implementation

1. Locate the active Forge bundle and state root with [references/forge-paths.md](references/forge-paths.md).
2. Inspect before changing:

```powershell
python <forge-bundle>/commands/resolve_preferences.py --format json
python <forge-bundle>/commands/resolve_preferences.py --workspace <workspace> --format json
```

3. Map the request onto canonical Forge fields only:
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
4. Choose scope deliberately:
   - `global` for host-wide defaults
   - `workspace` for repo-local overrides in `.brain/preferences.json`
   - `both` only when the user explicitly wants the same change in both scopes
5. Prefer the writer when scripts exist:

```powershell
python <forge-bundle>/commands/write_preferences.py --detail-level concise --pace fast --feedback-style direct --scope global --apply
python <forge-bundle>/commands/write_preferences.py --workspace <workspace> --language vi --orthography vietnamese_diacritics --scope workspace --apply
python <forge-bundle>/commands/write_preferences.py --workspace <workspace> --clear-field language --scope workspace --apply
```

6. If the scripts are unavailable, manually edit the canonical JSON described in [references/forge-preferences.md](references/forge-preferences.md):
   - `state/preferences.json` for host-wide defaults
   - `.brain/preferences.json` for workspace overrides
   - keep the object flat, valid UTF-8 JSON, and preserve unrelated keys
7. Keep the close-out short and operational:

```text
Changed:
- [...]

Scope:
- [...]

New style:
- [...]

Impact:
- [...]
```

## Example

User request:

```text
Only in this repo, answer in Vietnamese with diacritics and keep status updates short.
```

Apply the skill like this:

1. Inspect first so the workspace override is visible:

```powershell
python <forge-bundle>/commands/resolve_preferences.py --workspace <workspace> --format json
```

2. Map the request to canonical fields:
   - `language`: `vi`
   - `orthography`: `vietnamese_diacritics`
   - `custom_rules`: `["Keep status updates short and operational."]`
3. Persist only the repo-local override:

```powershell
python <forge-bundle>/commands/write_preferences.py --workspace <workspace> --language vi --orthography vietnamese_diacritics --scope workspace --apply
```

4. Close out briefly:

```text
Changed:
- Set `language` to `vi`
- Set `orthography` to `vietnamese_diacritics`

Scope:
- Workspace only

New style:
- Vietnamese with diacritics in this repo
- Shorter operational status updates

Impact:
- Other workspaces keep their current defaults
```

## Common Mistakes

- Guessing the active bundle or state root instead of using [references/forge-paths.md](references/forge-paths.md).
- Mutating state during inspection instead of using `resolve_preferences.py` as a read-only step.
- Inventing host-local keys or nested JSON instead of using the flat canonical Forge schema.
- Rewriting the whole preferences file for one field instead of changing only the requested keys.
- Treating `.brain/preferences.json` as legacy-only instead of a first-class workspace scope.
- Forgetting to use `--clear-field` when the task is to remove an override.

## References

- Read [references/forge-preferences.md](references/forge-preferences.md) for the canonical schema, scope rules, and field meanings.
- Read [references/forge-paths.md](references/forge-paths.md) to locate Forge bundles, scripts, and state roots across hosts.

## Integration

- Called by: natural-language requests to change durable Forge response preferences, language, orthography, tone, or pace.
- Calls next: `forge-session-management` when a repo or host should resume with the new durable style already applied.
- Pairs with: `forge-writing-skills` when the preference contract itself is being edited or hardened.
