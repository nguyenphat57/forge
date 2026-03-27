# UI Heuristics

> Global heuristics for frontend/visualize, not specific repo.

## Touch-Heavy UI

- Primary actions should be located in an easy-to-reach area, not close to the edge of the gesture if it is a mobile/tablet.
- Repetitive or high-frequency operations should have clear affordances and large targets.
- Don't design a flow that depends on hover if the main product is touching.

## Dense Data UI

- Group information into eye-catching semantic blocks, usually 5-9 main items per cluster.
- The primary KPI should stand out first. Secondary metrics can live in tabs, filters, or secondary rows.
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
- A safe default is 1, or at most 2, primary CTAs per view. Downgrade the rest or reveal them progressively.

## Accessibility Defaults

- Do not leave accessibility until the end. Focus order, contrast, labels, and motion boundaries should be visible from the brief/spec from the start.
