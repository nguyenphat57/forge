# UI Quality Checklist

> Checklist delivery is shared for `frontend` and `visualize`.

## Visual Direction

- [ ] Keep the existing design system or clearly state why it must be expanded
- [ ] Typography, color, intentional spacing
- [ ] Do not use emojis as UI icons
- [ ] Icon set consistently if there is an icon

## Interaction Quality

- [ ] Clickable surfaces have clear affordances
- [ ] Hover/focus states do not cause layout shift
- [ ] Cursor is suitable for interactive elements on the web
- [ ] No hover dependency for core behavior on touch surfaces

## States

- [ ] Default state is clear
- [ ] Loading state clearly
- [ ] Empty state clearly
- [ ] Error state is clear
- [ ] Destructive or confirm state clearly when needed

## Layout & Responsive

- [ ] Key breakpoints have been viewed
- [ ] No accidental horizontal scrolling on mobile
- [ ] Content is not covered by sticky/fixed elements
- [ ] Touch targets >= 44px for touch surfaces

## Contrast & Theming

- [ ] Text contrast is enough to read in light mode
- [ ] Surface and border are still visible in light mode
- [ ] Dark/light differences do not destroy hierarchy

## Motion

- [ ] Motion mainly uses `transform` and `opacity`
- [ ] Do not use `transition: all`
- [ ] Thinking about `prefers-reduced-motion`

## Accessibility

- [ ] Reasonable focus order
- [ ] Focus state is clear
- [ ] Form controls have labels or accessible names
- [ ] Do not use color as an indicator

## Anti-Patterns To Reject Fast

- Scale hover makes card jump layout
- Border is too blurry in light mode
- Body text is too light gray
- Just do the happy path and forget the system states
- Desktop-first design for touch-heavy screens
