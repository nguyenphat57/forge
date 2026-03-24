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
- Let `forge-codex` handle `help` and `next` from repo state directly; do not add a second recap workflow in local instructions.
- Let `forge-codex` handle `run` through the core run-guidance engine; do not invent a second layer that only repeats terminal output.
