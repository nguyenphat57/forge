---
name: init
type: flexible
triggers:
  - user wants to bootstrap a workspace for Forge
quality_gates:
  - Workspace is classified before suggesting the next workflow
  - No existing file is overwritten
  - Core stays host-neutral and avoids onboarding ceremony
---

# Init - Core Workspace Bootstrap

> Goal: bootstrap a minimal Forge workspace skeleton without pushing host-specific onboarding into `forge-core`.

<HARD-GATE>
- Do not overwrite existing files.
- Do not turn init into a long onboarding flow.
- Do not add host-specific aliases, ritual, or prose here.
</HARD-GATE>

## Process

1. Preview the skeleton first:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --format json
```

2. If the user wants the real skeleton written:

```powershell
python scripts/initialize_workspace.py --workspace <workspace> --seed-preferences --apply
```

3. End with one next workflow:
   - `brainstorm` for greenfield workspaces
   - `plan` for existing workspaces

Detailed semantics: see `references/workspace-init.md`.

## Activation Announcement

```text
Forge: init | bootstrap workspace, then choose one next workflow
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: init`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.
