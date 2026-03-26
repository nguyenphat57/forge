# UI Escalation Rules

> Used to decide when `frontend` or `visualize` should add `$ui-ux-pro-max`.

## Escalate To `$ui-ux-pro-max` When

- user wants more visual directions or style exploration
- visual direction is vague and needs reference breadth
- need palette / typography / landing pattern suggestions
- task is concept-first rather than implementation-first
- want to do extensive research before finalizing the brief

## Do Not Escalate When

- just a small CSS bug or spacing fix
- The existing design system is already clear and the task is just an implementation
- just need to fix small behavior/state in existing component
- The task is more about accessibility/responsive cleanup than visual exploration

## Recommended Order

### When the task is visualization-heavy

```text
1. visualize
2. If the visual direction is still large or the user wants many options -> load $ui-ux-pro-max
3. Finalize the visual brief
4. Handoff for frontend/build
```

### When the task is frontend but needs to open visual range

```text
1. frontend
2. If the design system is not directional enough -> load $ui-ux-pro-max
3. Update frontend brief
4. Implement UI
```

## Output Discipline

- `$ui-ux-pro-max` provides design exploration and breadth
- Forge `frontend`/`visualize` still keeps:
  - scope discipline
  - brief requirements
  - responsive/a11y/state coverage
  - handoff/report shape

Don't let `$ui-ux-pro-max` change Forge's brief or delivery checklist.
