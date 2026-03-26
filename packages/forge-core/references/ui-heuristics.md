# UI Heuristics

> Global heuristics for frontend/visualize, not specific repo.

## Touch-Heavy UI

- Primary actions should be located in an easy-to-reach area, not close to the edge of the gesture if it is a mobile/tablet.
- Repetitive or high-frequency operations should have clear affordances and large targets.
- Don't design a flow that depends on hover if the main product is touching.

## Dense Data UI

- Group information into eye-catching semantic blocks, usually 5-9 main items per cluster.
- Primary KPI must stand out first; Secondary metrics can go to tabs, filters, or secondary rows.
- Avoid noise such as heavy box-shadows, too bold borders, or every card "demanding attention".

## Dashboard UI

- Each first viewport should have a clear hierarchy: primary goal, primary KPI, primary action.
- Empty/loading/error of the dashboard must be designed like a real screen, not just empty space.
- Filters and time range controls need to be clear about what data they affect.

## Perceived Performance

- UI must respond quickly with skeleton, optimistic hint, disabled/loading state, or inline feedback.
- Animation cannot hide whether the app is slow or failing.

## Decision Architecture

- Avoid "wall of buttons".
- 1 or maximum 2 main CTAs per view is a safe default; the rest downgrade or progressive disclosure.

## Accessibility Defaults

- Don't wait until the end to think about accessibility; focus order, contrast, labels, and motion boundaries must appear immediately from the brief/spec.
