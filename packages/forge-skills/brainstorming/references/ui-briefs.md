# UI Briefs

> Use this file when the repo already contains persisted UI brief artifacts and the task needs to validate or interpret them. Forge no longer ships the older UI brief generator as part of the current kernel-only surface.

## Why This Still Exists

Persisted UI briefs remain useful as repo-local artifacts for:

- scope locking
- visual direction
- interaction model
- state coverage
- responsive boundaries
- accessibility notes

This file documents the artifact shape and current checker behavior. It does not describe an active Forge runtime-tool flow.

## Expected Artifact Shape

Historical or repo-local UI brief artifacts typically follow:

```text
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.md
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.json
.forge-artifacts/ui-briefs/<project-slug>/<mode>/pages/<screen>.md
```

Reading order:
1. `MASTER.md`
2. `pages/<screen>.md` when that screen has an override

## When To Reuse vs Rewrite

Reuse an existing brief when:

- the visual direction is unchanged
- the task stays within the same screen family
- stack and platform constraints are unchanged

Rewrite or replace the brief outside Forge when:

- new screens are added
- the visual direction changes materially
- the platform lens changes
- the repo needs a brand-new brief artifact rather than validation of an existing one

## Minimum Brief Quality

- clear scope
- explicit states: default, loading, empty, error
- responsive or platform notes
- accessibility boundaries
- stack-specific focus areas or watchouts

## Validate A Persisted Brief

```powershell
python commands/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
python commands/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/visualize --mode visualize --screen dashboard
```

`visualize` remains the compatibility brief mode name for the visual lens inside `brainstorm`.

## Historical Note

- If a historical workspace still carries packet-render or capture loops, treat them as archive context, not as current Forge guidance.

