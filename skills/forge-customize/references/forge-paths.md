# Forge Paths And Discovery

Use this file to locate Forge bundles, scripts, and state roots across hosts without assuming a single host surface.

## What To Find

For customization work, look for:

- a Forge bundle root containing `scripts/resolve_preferences.py`
- the matching `scripts/write_preferences.py`
- the state root that owns `state/preferences.json`

## Common Installed Locations

### Codex

- Bundle: `~/.codex/skills/forge-codex`
- State root: `~/.codex/forge-codex`
- Preferences file: `~/.codex/forge-codex/state/preferences.json`

### Antigravity

- Bundle: `~/.gemini/antigravity/skills/forge-antigravity`
- State root: `~/.gemini/antigravity/forge-antigravity`
- Preferences file: `~/.gemini/antigravity/forge-antigravity/state/preferences.json`

### Forge Core Installed Explicitly

- Bundle: whatever path the operator installed `forge-core` into
- State root: usually a sibling `forge-core-state`
- Preferences file: `<state-root>/state/preferences.json`

## Source Checkout

When working inside the Forge source repo:

- bundle-neutral scripts live under `packages/forge-core/scripts/`
- source-repo operator entrypoint is `python scripts/repo_operator.py customize --workspace <workspace> --format json`

Use the source checkout only when the task is inside that repo. For installed host work, prefer the installed bundle.

## Detection Order

1. If the current workspace is a Forge source checkout, use its canonical scripts.
2. Otherwise look for an installed host bundle in known skill locations.
3. If neither exists, fall back to manual editing of canonical JSON files.

## Manual Fallback Targets

- host-wide: `state/preferences.json`
- workspace-local: `.brain/preferences.json`

Only use manual fallback when you cannot find `resolve_preferences.py` and `write_preferences.py`.
