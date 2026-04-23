- source-repo durable preference entrypoint is natural language plus `commands/resolve_preferences.py` and `commands/write_preferences.py`

## Forge Paths

- Source repo canonical sibling skill source is `packages/forge-skills/customize/`.
- Adapter-global preferences persist in `state/preferences.json` under the active Forge bundle state root.
- Workspace-local overrides persist in `.brain/preferences.json` under the current workspace.
- Forge customize commands are owned by `packages/forge-skills/customize/commands/` in source and materialized into the active Forge bundle `commands/` directory:
  - `resolve_preferences.py`
  - `write_preferences.py`
- Installed Codex bundle root defaults to `$CODEX_HOME/skills/forge-codex`.
- Installed Antigravity bundle root defaults to `$GEMINI_HOME/antigravity/skills/forge-antigravity`.
