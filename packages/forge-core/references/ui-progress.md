# UI Progress Tracking

> Used for long frontend/visualize tasks, multiple screens, or multiple handoffs.

## Why

Forge route is good but long UI tasks often drift easily:
- Have you finalized the brief yet?
- Are you in interaction model or implementation?
- Have you reviewed responsive/a11y yet?

Artifact progress helps avoid ambiguity without the need for a large dashboard.

## Command

### Frontend

```powershell
python scripts/track_ui_progress.py "Checkout tablet refresh" --mode frontend --stage implementation --status active
```

### Visualize

```powershell
python scripts/track_ui_progress.py "Kitchen dashboard exploration" --mode visualize --stage interaction-model --status active
```

Default Artifact:

```text
.forge-artifacts/ui-progress/<mode>/<task>.md
.forge-artifacts/ui-progress/<mode>/<task>.json
```

## Recommended Stages

### frontend

- `brief`
- `system-check`
- `implementation`
- `responsive-a11y-review`
- `handover`

### visualize

- `brief`
- `interaction-model`
- `spec-or-mockup`
- `states-platform-review`
- `handover`

## Use Rule

- Not required for small tasks.
- Should be used when the UI task spans multiple messages, multiple screens, or is easy to handoff between design and implementation.
