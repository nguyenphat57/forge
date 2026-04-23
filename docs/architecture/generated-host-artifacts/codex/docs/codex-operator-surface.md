# Codex Operator Surface

## Natural-Language First

Preferred user phrasing:

{{FORGE_CODEX_NATURAL_LANGUAGE_EXAMPLES}}

Session requests:

{{FORGE_CODEX_SESSION_REQUEST_EXAMPLES}}

## Codex Rules

- Natural language is the primary surface.
- Explicit operator action names such as `bump` or `delegate` are acceptable when a concise form helps.
- Guidance, next-step selection, and command execution stay natural-language first through Forge skills and host-native tools.
- Wrapper docs may clarify output shape, but they must not fork core semantics.
- Do not add heavy session wrappers or onboarding ceremony here.
- `AGENTS.md` should stay thin and point back to Forge instead of duplicating logic.
