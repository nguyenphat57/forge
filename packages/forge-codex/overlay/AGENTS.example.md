# Codex Workspace Entry

Use `forge-codex` as the global orchestrator for this workspace.

## Read order

1. Read this `AGENTS.md`.
2. Load `forge-codex`.
3. If the workspace has local companions, route through `.agent/router.md` or the workspace skill map.

## Notes

- Keep `AGENTS.md` thin.
- Put routing detail in the workspace router doc.
- Do not duplicate Forge orchestration rules inside local skills.
- Prefer natural-language requests first; keep slash forms only as optional aliases.
- Good entrypoints:
  - "Help me figure out the next step"
  - "Run `npm test` and tell me what to do after"
  - "Bump this to 0.5.0"
  - "We need to roll back the last deploy"
  - "Give shorter answers and move faster"
  - "Bootstrap this workspace for Forge"
- If `.brain/preferences.json` exists, let `forge-codex` resolve it through the core preferences engine instead of redefining response-style rules here.
- If the user wants durable preference changes, let `forge-codex` persist them through `scripts/write_preferences.py`, not a host-local schema.
- Let `forge-codex` handle `help` and `next` from repo state directly; do not add a second recap workflow in local instructions.
- Let `forge-codex` handle `run` through the core run-guidance engine; do not invent a second layer that only repeats terminal output.
- Let `forge-codex` keep `bump` and `rollback` natural-language first, but still route through the core explicit release/rollback planners.
- Let `forge-codex` keep `customize` and `init` thin; do not add heavy onboarding or memory rituals around them.
- If the user asks to bootstrap a workspace, keep the UX thin but still route through `scripts/initialize_workspace.py`.
