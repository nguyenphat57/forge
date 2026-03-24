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
- If `.brain/preferences.json` exists, let `forge-codex` resolve it through the core preferences engine instead of redefining response-style rules here.
- If the user wants durable preference changes, let `forge-codex` persist them through `scripts/write_preferences.py`, not a host-local schema.
- Let `forge-codex` handle `help` and `next` from repo state directly; do not add a second recap workflow in local instructions.
- Let `forge-codex` handle `run` through the core run-guidance engine; do not invent a second layer that only repeats terminal output.
- Let `forge-codex` keep `bump` and `rollback` natural-language first, but still route through the core explicit release/rollback planners.
- If the user asks to bootstrap a workspace, keep the UX thin but still route through `scripts/initialize_workspace.py`.
