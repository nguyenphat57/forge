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
- If the user wants durable preference changes, let `forge-codex` persist them through sibling skill `forge-customize`, not a host-local schema.
- If the workspace needs durable language rules such as "always reply in Vietnamese with full diacritics", persist them through sibling skill `forge-customize` in adapter-global Forge state. Use `.brain/preferences.json` only for workspace-specific overrides; otherwise let `forge-codex` default to English.
- Let `forge-codex` handle guidance, next-step selection, and command execution through natural language, Forge skills, and host-native tools.
- If boundaries are clear and the host can delegate safely, let `forge-codex` invoke `forge-dispatching-parallel-agents` instead of improvising parallel edits.
- Let `forge-codex` keep `bump` natural-language first without reintroducing extra operator ceremony.
- Let `forge-codex` route durable preference changes through `forge-customize`, and route bootstrap requests to `forge-init`.
- If the user asks to bootstrap a workspace, keep the UX thin and route directly to the sibling skill owner `forge-init`.

