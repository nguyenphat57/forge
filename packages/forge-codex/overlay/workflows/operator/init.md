---
name: init
type: flexible
triggers:
  - natural-language request to bootstrap a workspace for Forge
  - optional alias: /init
quality_gates:
  - Workspace is classified before suggests a next step
  - No existing file is overwritten
  - Wrapper stays thin and avoids onboarding ceremony
---

# Init - Codex Workspace Bootstrap

> Goal: give Codex a minimal initial flow to start a new workspace without turning it into a lengthy onboarding.

## Process

1. Preview skeleton:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --format json
```

2. If you need to create a real skeleton:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

`--seed-preferences` will seed Codex-global preferences, no longer writing to workspace-local `.brain/preferences.json`.

3. Finish with a single next workflow:
   - `brainstorm` for greenfield workspace
   - `plan` for existing workspace

## Activation Announcement

```text
Forge Codex: init | bootstrap workspace with one next step
```
