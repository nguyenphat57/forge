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

| Command | Workflow |
|---------|----------|
| `/brainstorm` | `design/brainstorm.md` |
| `/plan` | `design/plan.md` |
| `/design` | `design/architect.md` |
| `/visualize` | `design/visualize.md` |
| `/code` | `execution/build.md` |
| `/debug` | `execution/debug.md` |
| `/test` | `execution/test.md` |
| `/review` | `execution/review.md` |
| `/refactor` | `execution/refactor.md` |
| `/deploy` | `execution/deploy.md` |
| `/help` | `operator/help.md` |
| `/next` | `operator/next.md` |
| `/run` | `operator/run.md` |
| `/delegate` | `execution/dispatch-subagents.md` |
| `/bump` | `operator/bump.md` |
| `/rollback` | `operator/rollback.md` |
| `/customize` | `operator/customize.md` |
| `/init` | `operator/init.md` |

## Global Rules

- Natural language is the primary surface. Slash commands are optional aliases.
- Use Vietnamese for user-facing communication unless the user switches language.
- Keep `forge-codex` as the base orchestrator for all work in this host.
- Prefer repo state, plans, specs, and workspace-local `.brain/` artifacts over legacy session rituals or host-global state files.
- Let workspace-local routers extend Forge, not replace it.
- Do not suggest legacy session rituals as default guidance.
- Durable preferences live in workspace-local `.brain/preferences.json`.

<!-- FORGE CODEX GLOBAL END -->
