---
name: init
type: flexible
triggers:
  - first-run workspace bootstrap
quality_gates:
  - Workspace is classified as greenfield or existing before suggesting next steps
  - No existing file is overwritten
  - Ends with one recommended next workflow
---

# Init - Antigravity Workspace Bootstrap

> Goal: keep workspace bootstrap requests clear without pushing host ceremony into core.

<HARD-GATE>
- Do not overwrite existing files.
- Do not turn init into a lengthy onboarding.
- Do not embed host-specific slash surface into the core script.
</HARD-GATE>

## Process

1. Preview skeleton:

```powershell
python commands/initialize_workspace.py --workspace <workspace> --format json
```

2. If the user wants to create the actual skeleton:

```powershell
python commands/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

`--seed-preferences` seeds Antigravity-global preferences; it no longer writes to workspace-local `.brain/preferences.json`.

3. If the user wants to personalize immediately, switch to the `customize` action.
4. End with a single next workflow:
   - `brainstorm` for greenfield workspaces
   - `plan` for existing workspaces

## Output Contract

```text
Initialized: [...]
Mode: [...]
Next: [...]
```

## Activation Announcement

```text
Forge Antigravity: init | bootstrap workspace, then choose one next workflow
```
