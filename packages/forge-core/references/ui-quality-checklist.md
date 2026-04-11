# UI Quality Checklist

> This delivery checklist is shared by UI implementation and `visualize`.

## Visual Direction

- [ ] Keep the existing design system or clearly state why it must be expanded
- [ ] Typography, color, intentional spacing
- [ ] Do not use emojis as UI icons
- [ ] Iconography is consistent if icons are used

## Interaction Quality

- [ ] Clickable surfaces have clear affordances
- [ ] Hover/focus states do not cause layout shift
- [ ] Cursor is suitable for interactive elements on the web
- [ ] No hover dependency for core behavior on touch surfaces

## States

- [ ] Default state is clear
- [ ] Loading state is clear
- [ ] Empty state is clear
- [ ] Error state is clear
- [ ] Destructive or confirmation states are clear when needed

## Layout & Responsive

- [ ] Key breakpoints have been viewed
- [ ] No accidental horizontal scrolling on mobile
- [ ] Content is not covered by sticky/fixed elements
- [ ] Touch targets >= 44px for touch surfaces

## Contrast & Theming

- [ ] Text contrast is readable in light mode
- [ ] Surfaces and borders remain visible in light mode
- [ ] Dark/light differences do not destroy hierarchy

## Motion

- [ ] Motion mainly uses `transform` and `opacity`
- [ ] Do not use `transition: all`
- [ ] `prefers-reduced-motion` has been considered

## Accessibility

- [ ] Reasonable focus order
- [ ] Focus state is clear
- [ ] Form controls have labels or accessible names
- [ ] Do not use color as an indicator

## Anti-Patterns To Reject Fast

- Hover scale makes cards jump in layout
- Borders are too faint in light mode
- Body text is too light gray
- Only the happy path is designed while system states are ignored
- Desktop-first design is used for touch-heavy screens
