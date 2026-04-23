# Codex Workspace Entry

Forge is the evidence-first execution kernel for this workspace. Keep this entry thin and let the bundle own sibling skill activation, verification, and packet semantics.

Use `forge-codex` as the global orchestrator for this workspace.

## Read Order

1. Read this `AGENTS.md`.
2. Load `forge-codex`.
3. If the workspace has local companions, treat them as augmentation over Forge sibling skills.

## Notes

- Keep `AGENTS.md` thin.
- Put repo-specific conventions in local docs, not a competing router.
- Do not duplicate Forge orchestration rules inside local skills.
- Prefer natural-language requests first. Use plain action names or explicit skill names when a concise form helps.
- Suggested prompts:
  - "Help me figure out the next step"
  - "Run `npm test` and tell me what to do after"
  - "Split the independent failures across subagents where safe"
  - "Bump this to 0.5.0"
  - "We need to roll back the last deployment"
  - "Use shorter answers and move faster by default"
  - "Bootstrap this workspace for Forge with canonical docs"
- Let `forge-codex` resolve response-style preferences through the adapter-global Forge preferences engine instead of redefining response-style rules here.
- If the user wants durable preference changes, let `forge-codex` persist them through `commands/write_preferences.py`, not a host-local schema.
- If the workspace needs durable language rules such as "always reply in Vietnamese with full diacritics", persist them through `commands/write_preferences.py` in adapter-global Forge state. Use `.brain/preferences.json` only for workspace-specific overrides; otherwise let `forge-codex` default to English.
- Let `forge-codex` handle `help` and `next` directly from repo state. Do not add a second session-restore workflow in local instructions.
- Let `forge-codex` handle `run` through the core run-guidance engine. Do not invent a second layer that only repeats terminal output.
- If boundaries are clear and the host can delegate safely, let `forge-codex` invoke `forge-dispatching-parallel-agents` instead of improvising parallel edits.
- Let `forge-codex` keep `bump` natural-language first without reintroducing extra operator ceremony.
- Let `forge-codex` route durable preference changes through `forge-customize` and `commands/write_preferences.py`, and route bootstrap requests to `forge-init`.
- If the user asks to bootstrap a workspace, keep the UX thin but still let `forge-init` call `commands/initialize_workspace.py`.

