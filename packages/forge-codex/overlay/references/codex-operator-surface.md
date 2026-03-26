# Codex Operator Surface

## Natural-Language First

Preferred user phrasing:

- "Help me figure out the next step" -> `help`
- "What should I do next?" -> `next`
- "Run `npm test` and tell me what to do after" -> `run`
- "Split these independent slices across subagents" -> `delegate`
- "Bump this to 0.5.0" -> `bump`
- "We need to roll back the last deployment" -> `rollback`
- "Give shorter answers and move faster" -> `customize`
- "Bootstrap this workspace for Forge" -> `init`

Optional aliases:

- `/help`
- `/next`
- `/run`
- `/delegate`
- `/bump`
- `/rollback`
- `/customize`
- `/init`

## Codex Rules

- Natural language is the primary surface; aliases are optional.
- Wrapper docs may clarify output shape, but they must not fork core semantics.
- Do not add heavy session wrappers or onboarding ceremony here.
- `AGENTS.md` should stay thin and point back to Forge instead of duplicating logic.
- `dispatch-subagents` is a Codex runtime adapter: it maps Forge lane policy to native Codex subagents, not a replacement for core build/debug/review workflows.
