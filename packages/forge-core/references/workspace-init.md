# Forge Workspace Init

> Goal: keep the workspace initialization at `forge-core` in a host-neutral fashion, so that the adapter only needs to add the `/init` wrapper and onboarding without forking the skeleton logic.

## Core Contract

- Script canonical is located at `scripts/initialize_workspace.py`
- This script only creates a minimal Forge skeleton that can be reused across multiple hosts
- Adapter can add first-run UX, but cannot change the shape of `.brain/` or the docs skeleton that the core has fixed

## Minimum Skeleton

- `.brain/`
- `.brain/session.json`
- `docs/plans/`
- `docs/specs/`

Options:

- adapter-global `state/preferences.json` if wrapper wants to seed default preferences at init

## Workspace Classification

- `greenfield`: workspace is empty or has no significant state repo -> default next workflow is `brainstorm`
- `existing`: workspace already has repo state -> default next workflow is `plan`

## Hard Rules

- Do not overwrite existing files
- Do not embed host-specific onboarding prose into core script
- Do not create a host's own README, command alias, or memory ritual in this script

## Adapter Boundary

- `forge-antigravity`: can include `/init` + thin onboarding based on this script
- `forge-codex`: can expose minimal init via natural language without needing a heavy ceremony
- Future adapters like `forge-claude` must be able to reuse this script without changing the schema or layout files
