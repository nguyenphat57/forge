# Antigravity Operator Surface

## Primary Wrappers

{{FORGE_ANTIGRAVITY_PRIMARY_WRAPPER_TABLE}}

## Compatibility Wrappers

{{FORGE_ANTIGRAVITY_COMPATIBILITY_WRAPPER_TABLE}}

Legacy session aliases stay available for one stable line and should emit a deprecation warning instead of behaving like a primary surface.

## Compatibility Rules

- Wrapper docs may use a more operator-friendly presentation.
- Core semantics, schema, and deterministic scripts must not be forked.
- Aliases exist only to reduce migration friction from AWF or older Antigravity versions; they do not create new intents.
