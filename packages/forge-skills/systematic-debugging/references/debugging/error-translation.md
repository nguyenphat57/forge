# Forge Error Translation

> Use when you need to turn stderr/raw error into a more readable summary, but still retain enough technical context for further debugging.

## Target

- Match common error patterns deterministically
- redact secrets, tokens, and sensitive paths before displaying them again
- Returns `human_message` + `suggested_action` so that `run`, `debug`, `build`, and `test` can be reused

## Canonical Script

```powershell
python commands/translate_error.py --error-text "Module not found: payments.service"
python commands/translate_error.py --input-file C:\path\to\stderr.txt --format json
```

## Output Contract

- `status`: `PASS` if match known pattern, `WARN` if fallback generic
- `translation.category`
- `translation.human_message`
- `translation.suggested_action`
- `translation.error_excerpt` after redact

## Current Categories

- `module`
- `database`
- `runtime`
- `network`
- `timeout`
- `test`
- `build`
- `git`
- `deploy`
- `generic`

## Boundary

- Core only takes care of basic deterministic translation and sanitation.
- The adapter can change the way it is presented to the user, but cannot fork the database pattern or category semantics.
- If a new pattern is needed, add it to the core instead of patching it separately in each host.

