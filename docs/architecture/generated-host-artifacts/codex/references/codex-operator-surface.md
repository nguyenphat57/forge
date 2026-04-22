# Codex Operator Surface

## Natural-Language First

Preferred user phrasing:

{{FORGE_CODEX_NATURAL_LANGUAGE_EXAMPLES}}

Optional aliases:

{{FORGE_CODEX_OPTIONAL_ALIASES}}

Session requests:

{{FORGE_CODEX_SESSION_REQUEST_EXAMPLES}}

## Codex Rules

- Natural language is the primary surface. Aliases are optional.
- Wrapper docs may clarify output shape, but they must not fork core semantics.
- Do not add heavy session wrappers or onboarding ceremony here.
- `AGENTS.md` should stay thin and point back to Forge instead of duplicating logic.
- `/delegate` is a compatibility alias for `forge-dispatching-parallel-agents`: it maps Forge lane policy to native Codex subagents without replacing sibling build/debug/review skills.
