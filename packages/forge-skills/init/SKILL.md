---
name: forge-init
description: Use when bootstrapping Forge project docs and workspace skeletons, or when normalizing an existing repo into the Forge bootstrap docs standard.
---

# Forge Init

<EXTREMELY-IMPORTANT>
Bootstrap docs are project knowledge, not execution memory.

Do not turn bootstrap docs into `.brain`, handover, workflow-state, or session ceremony.

Preview first. Apply after inspecting the current workspace.
</EXTREMELY-IMPORTANT>

## Use When

- The user asks to bootstrap a new workspace for Forge.
- An existing repo needs `AGENTS.md`, `docs/PRODUCT.md`, `docs/STACK.md`, or other Forge bootstrap docs.
- Existing docs should be merged or normalized into the Forge bootstrap docs standard.
- You need a thin project contract before `brainstorm` or `plan`.

## Do Not Use When

- The task is session restore, save context, or handover; use `forge-session-management`.
- The user wants feature design, bug investigation, or implementation work after bootstrap already exists.
- The request is only to inspect or explain docs without creating or normalizing bootstrap artifacts.

## Blueprint Contract

- Canonical reference: `references/project-docs-blueprint.md`
- Default bootstrap docs:
  - `AGENTS.md`
  - `docs/PRODUCT.md`
  - `docs/STACK.md`
- Optional docs when repo signals justify them:
  - `docs/ARCHITECTURE.md`
  - `docs/QUALITY.md`
  - `docs/SCHEMA.md`
  - `docs/OPERATIONS.md`
  - `docs/CHANGELOG.md`
  - `docs/templates/FEATURE_TASK.md`
- Do not create `docs/STATUS.md`, `docs/DECISIONS.md`, or `docs/ERRORS.md` by default.

## Process Flow

1. Inspect the workspace first.
2. Load `references/project-docs-blueprint.md`.
3. Preview the bootstrap plan through:

```powershell
python commands/initialize_workspace.py --workspace <workspace> --format json
```

4. Apply the plan only when bootstrap or normalization is actually wanted:

```powershell
python commands/initialize_workspace.py --workspace <workspace> --apply --format json
```

5. End with exactly one next workflow:
   - `brainstorm` for `greenfield`
   - `plan` for every existing workspace mode

## Merge And Normalize Rules

- Reuse canonical docs when they already exist.
- Normalize from equivalent docs when the canonical path is missing.
- Do not overwrite existing user files just to force the canonical layout.
- Keep `.brain` and `.forge-artifacts/workflow-state` outside the bootstrap docs layer.

## Placeholder Contract

When data is missing, use only:

- `[NEEDS INPUT: ...]`
- `[TO BE CONFIRMED: ...]`

## Integration

- Called by: natural-language bootstrap requests and explicit `forge-init` activation.
- Uses: `references/project-docs-blueprint.md` and `python commands/initialize_workspace.py`.
- Calls next: `forge-brainstorming` for greenfield workspaces, `forge-writing-plans` or plan-mode work for existing repos.
- Pairs with: `forge-session-management` after bootstrap when continuity needs to be saved or restored.
