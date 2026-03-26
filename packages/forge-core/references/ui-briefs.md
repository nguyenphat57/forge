# UI Briefs

> Use when the task is `frontend` or `visualize` at a medium/large level, or when the visual instructions are ambiguous.

## Why This Exists

`frontend` and `visualize` both need a clear first artifact before diving into the component or mockup:

- `frontend`: frontend brief
- `visualize`: visual brief

This brief did not change the project's design system. It just latches:
- scope. scope
- visual direction
- interaction model
- states. states
- responsive/a11y boundaries
- stack/platform lens

## Generate A Brief

### Frontend brief

```powershell
python scripts/generate_ui_brief.py "Refresh checkout layout for tablet POS" `
  --mode frontend `
  --stack react-vite `
  --platform tablet `
  --screen checkout
```

### Visual brief

```powershell
python scripts/generate_ui_brief.py "Explore a calmer dashboard direction for kitchen mode" `
  --mode visualize `
  --stack mobile-webview `
  --platform tablet `
  --screen kitchen-dashboard
```

## Persisted Master + Page Override Pattern

When the task spans multiple steps or screens, add `--persist`:

```powershell
python scripts/generate_ui_brief.py "..." --mode frontend --persist --project-name "LamDiFood POS" --screen checkout
```

Artifact generates:

```text
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.md
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.json
.forge-artifacts/ui-briefs/<project-slug>/<mode>/pages/<screen>.md
```

Reading order:
1. `MASTER.md`
2. `pages/<screen>.md` if screen has override

## When To Reuse vs Regenerate

Reuse brief is available when:
- visual direction remains unchanged
- same screen family
- same stack/platform constraints

Regenerate or update brief when:
- added new screens
- change visual direction
- change lens platform
- task moves from concept to implementation or vice versa

## Minimum Brief Quality

- Have a clear scope
- Have clear states: default/loading/empty/error
- Have responsive or platform notes
- Has accessibility boundary
- Has stack-specific focus or watchouts

## Validate A Persisted Brief

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
```

Or:

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/visualize --mode visualize --screen dashboard
```
