# UI Briefs

> Use this file when the task is `frontend` or `visualize` at medium or large scope, or when the visual direction is still ambiguous.

## Why This Exists

`frontend` and `visualize` both need a clear artifact before jumping into components or mockups:

- `frontend`: a frontend brief
- `visualize`: a visual brief

The brief does not redefine the project's design system. It locks:
- scope
- visual direction
- interaction model
- states
- responsive and accessibility boundaries
- stack and platform lens

## Generate a Brief

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

Generated artifacts:

```text
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.md
.forge-artifacts/ui-briefs/<project-slug>/<mode>/MASTER.json
.forge-artifacts/ui-briefs/<project-slug>/<mode>/pages/<screen>.md
```

Reading order:
1. `MASTER.md`
2. `pages/<screen>.md` when that screen has an override

## When to Reuse vs Regenerate

Reuse an existing brief when:
- the visual direction is unchanged
- the task stays within the same screen family
- stack and platform constraints are unchanged

Regenerate or update the brief when:
- you add new screens
- the visual direction changes
- the platform lens changes
- the task moves from concept to implementation, or the reverse

## Minimum Brief Quality

- Clear scope
- Explicit states: default, loading, empty, error
- Responsive or platform notes
- Accessibility boundaries
- Stack-specific focus areas or watchouts

## Validate a Persisted Brief

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/frontend --mode frontend --screen checkout
```

Or:

```powershell
python scripts/check_ui_brief.py .forge-artifacts/ui-briefs/<project-slug>/visualize --mode visualize --screen dashboard
```

## Optional Design Packet Runtime

If `forge-design` is installed, a persisted brief can be turned into a reviewable HTML artifact:

```powershell
python scripts/invoke_runtime_tool.py forge-design render-brief .forge-artifacts/ui-briefs/<project-slug>/visualize --screen dashboard
```

The resulting packet is useful for review, handoff, or capture with `forge-browse`.

If both runtime tools are installed, a minimal capture loop is:

```powershell
python scripts/invoke_runtime_tool.py forge-browse session-create --label "design-review" --format json
python scripts/invoke_runtime_tool.py forge-browse snapshot --session <session-id> --url file:///C:/path/to/review-packet.html --output C:\path\to\review-packet.png
```
