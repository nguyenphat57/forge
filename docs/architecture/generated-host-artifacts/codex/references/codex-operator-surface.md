# Codex Operator Surface

## Natural-Language First

Preferred user phrasing:

{{FORGE_CODEX_NATURAL_LANGUAGE_EXAMPLES}}

Optional aliases:

{{FORGE_CODEX_OPTIONAL_ALIASES}}

## Codex Rules

- Natural language is the primary surface. Aliases are optional.
- Wrapper docs may clarify output shape, but they must not fork core semantics.
- Do not add heavy session wrappers or onboarding ceremony here.
- `AGENTS.md` should stay thin and point back to Forge instead of duplicating logic.
- `dispatch-subagents` is a Codex runtime adapter: it maps Forge lane policy to native Codex subagents, not a replacement for core build/debug/review workflows.
