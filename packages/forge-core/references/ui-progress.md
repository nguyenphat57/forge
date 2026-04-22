# UI Progress Tracking

> Use this for long frontend or visual-lens tasks, multiple screens, or repeated handoffs.

## Why

Forge routes well, but long UI tasks drift easily:
- Has the brief been finalized?
- Are you still in interaction-model work, or already in implementation?
- Has responsive/accessibility review happened yet?

Progress artifacts reduce ambiguity without requiring a large dashboard.

## Command

### Frontend

```powershell
python scripts/track_ui_progress.py "Checkout tablet refresh" --mode frontend --stage implementation --status active
```

### Visual Lens Compatibility Mode

```powershell
python scripts/track_ui_progress.py "Kitchen dashboard exploration" --mode visualize --stage interaction-model --status active
```

Default artifacts:

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

`visualize` is the compatibility mode name for progress artifacts that support the visual lens inside `brainstorm`.

- `brief`
- `interaction-model`
- `spec-or-mockup`
- `states-platform-review`
- `handover`

## Use Rule

- Not required for small tasks.
- Use it when the UI task spans multiple messages, multiple screens, or is likely to hand off between design and implementation.
