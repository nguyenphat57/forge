# UI Good / Bad Examples

> Used when you want to drag the anti-pattern from the "rule" level to the "easy to recognize" level.

## Hover Stability

Bad:

```css
.card:hover {
  transform: scale(1.04);
}
```

Problem:
- jump card layout
- list/grid alignment shakes easily
- touch devices do not benefit at all

Good:

```css
.card {
  transition: box-shadow 180ms ease, border-color 180ms ease, background-color 180ms ease;
}

.card:hover,
.card:focus-within {
  border-color: var(--color-border-strong);
  box-shadow: 0 8px 24px rgb(0 0 0 / 0.08);
}
```

## State Coverage

Bad:

```tsx
return <OrderList orders={orders} />;
```

Problem:
- no loading
- no empty state
- fetch error has no place to appear

Good:

```tsx
if (isLoading) return <OrdersSkeleton />;
if (error) return <InlineError message="Could not load orders" />;
if (orders.length === 0) return <EmptyState title="No orders yet" />;

return <OrderList orders={orders} />;
```

## Touch-Heavy Actions

Bad:

```tsx
<button className="h-8 px-2">Pay now</button>
```

Problem:
- target is too small to touch
- hierarchy is weak if action is primary

Good:

```tsx
<button className="min-h-[44px] px-4 text-sm font-medium">
  Pay now
</button>
```

## Visual Direction Drift

Bad:

```text
Small task in the existing app, but automatically changes the entire typography and CTA color.
```

Problem:
- destroy design system
- increased blast radius unnecessarily

Good:

```text
Keep the existing tokens and typography. Open a new visual direction only when the brief clearly explains why.
```

## Dense Dashboard Layout

Bad:

```text
Stuff 14 metric cards, 3 charts, 2 filters and 4 CTAs into the first viewport.
```

Problem:
- Hick's Law and Miller's Law are broken
- no longer has primary focus

Good:

```text
Group metrics into 5-7 main items, secondary insights below the fold or into tab/filter.
```
