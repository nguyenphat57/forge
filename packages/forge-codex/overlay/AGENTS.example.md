# Codex Workspace Entry

Forge is the process-first execution system for this workspace. Keep this entry thin and let the bundle own routing, verification, and packet semantics.

Use `forge-codex` as the global orchestrator for this workspace.

## Read Order

1. Read this `AGENTS.md`.
2. Load `forge-codex`.
3. If the workspace has local companions, route through `.agent/router.md` or the workspace skill map.

## Notes

- Keep `AGENTS.md` thin.
- Put routing details in the workspace router doc.
- Do not duplicate Forge orchestration rules inside local skills.
- Prefer natural-language requests first. Keep slash forms only as optional aliases.
- Suggested prompts:
  - "Help me figure out the next step"
  - "Run `npm test` and tell me what to do after"
  - "Split the independent failures across subagents where safe"
  - "Bump this to 0.5.0"
  - "We need to roll back the last deployment"
  - "Give shorter answers and move faster"
  - "Bootstrap this workspace for Forge"
- Let `forge-codex` resolve response-style preferences through the adapter-global Forge preferences engine instead of redefining response-style rules here.
- If the user wants durable preference changes, let `forge-codex` persist them through `scripts/write_preferences.py`, not a host-local schema.
- If the workspace needs durable language rules such as "always reply in Vietnamese with full diacritics", persist them through `scripts/write_preferences.py` in adapter-global Forge state. Use `.brain/preferences.json` only for workspace-specific overrides; otherwise let `forge-codex` default to English.
- Let `forge-codex` handle `help` and `next` directly from repo state. Do not add a second session-restore workflow in local instructions.
- Let `forge-codex` handle `run` through the core run-guidance engine. Do not invent a second layer that only repeats terminal output.
- If boundaries are clear and the host can delegate safely, let `forge-codex` load `dispatch-subagents` instead of improvising parallel edits.
- Let `forge-codex` keep `bump` and `rollback` natural-language first, but still route through the core explicit release/rollback planners.
- Let `forge-codex` keep `customize` and `init` thin. Do not add heavy onboarding or memory rituals around them.
- If the user asks to bootstrap a workspace, keep the UX thin but still route through `scripts/initialize_workspace.py`.
