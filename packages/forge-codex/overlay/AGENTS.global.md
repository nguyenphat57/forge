<!-- FORGE CODEX GLOBAL START -->
# Forge Codex

Use `forge-codex` as the only global orchestrator for Codex.

## Read Order

1. Read this global `AGENTS.md`.
2. Load `{{FORGE_CODEX_SKILL}}`.
3. If the workspace has its own `AGENTS.md` or router doc, treat it as local augmentation on top of Forge.

## Command Aliases

When the user types one of the slash commands below, treat it as a workflow alias, not a filesystem path.
Read the mapped workflow from `{{FORGE_CODEX_WORKFLOWS}}`.

|Command | Workflow|
|---------|----------|
|`/brainstorm` | `design/brainstorm.md`|
|`/plan` | `design/plan.md`|
|`/design` | `design/architect.md`|
|`/visualize` | `design/visualize.md`|
|`/code` | `execution/build.md`|
|`/debug` | `execution/debug.md`|
|`/test` | `execution/test.md`|
|`/review` | `execution/review.md`|
|`/refactor` | `execution/refactor.md`|
|`/deploy` | `execution/deploy.md`|
|`/help` | `operator/help.md`|
|`/next` | `operator/next.md`|
|`/run` | `operator/run.md`|
|`/delegate` | `execution/dispatch-subagents.md`|
|`/bump` | `operator/bump.md`|
|`/rollback` | `operator/rollback.md`|
|`/customize` | `operator/customize.md`|
|`/init` | `operator/init.md`|

## Global Rules

- Natural language is the primary surface. Slash commands are optional aliases.
- Default to English for user-facing communication unless resolved preferences require another language.
- When responding in Vietnamese, always use full Vietnamese diacritics and standard spelling.
- Never intentionally strip Vietnamese diacritics in user-facing text, comments, summaries, plans, or review notes.
- If shell or file content appears mojibake or accent-stripped, treat that as an encoding issue and restore it in valid UTF-8 Vietnamese instead of copying the corruption.
- Prefer UTF-8 for generated text that contains Vietnamese.
- Keep `forge-codex` as the base orchestrator for all work in this host.
- Prefer repo state, plans, specs, and scoped workspace `.brain/` continuous artifacts over legacy session rituals.
- Let workspace-local routers extend Forge, not replace it.
- Do not suggest legacy session rituals as default guidance.
- Durable preferences live in Codex-global adapter state at `~/.codex/forge-codex/state/preferences.json` (or `$FORGE_HOME/state/preferences.json` when overridden).

<!-- FORGE CODEX GLOBAL END -->
