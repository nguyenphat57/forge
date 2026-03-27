# Forge Workspace Init

> Goal: keep workspace initialization in `forge-core` host-neutral, so adapters only need a thin `/init` wrapper and onboarding layer without forking the skeleton logic.

## Core Contract

- The canonical script lives at `scripts/initialize_workspace.py`
- The script creates only a minimal Forge skeleton that can be reused across hosts
- Adapters may add first-run UX, but they must not change the shape of `.brain/` or the docs skeleton fixed by core

## Minimum Skeleton

- `.brain/`
- `.brain/session.json`
- `docs/plans/`
- `docs/specs/`

Options:

- adapter-global split preferences state (`state/preferences.json` + `state/extra_preferences.json`) if the wrapper wants to seed default preferences at init

## Workspace Classification

- `greenfield`: the workspace is empty or has no significant repo state -> default next workflow is `brainstorm`
- `existing`: the workspace already has repo state -> default next workflow is `plan`

## Hard Rules

- Do not overwrite existing files
- Do not embed host-specific onboarding prose into core script
- Do not create a host's own README, command alias, or memory ritual in this script

## Adapter Boundary

- Host adapters can include `/init` plus thin onboarding based on this script
- The active host adapter can expose minimal init through natural language without adding heavy ceremony
- Future adapters must be able to reuse this script without changing the schema or layout files
