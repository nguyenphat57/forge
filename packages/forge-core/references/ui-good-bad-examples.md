# UI Good / Bad Examples

> Dùng khi muốn kéo anti-pattern từ level “rule” xuống level “dễ nhận ra”.

## Hover Stability

Bad:

```css
.card:hover {
  transform: scale(1.04);
}
```

Vấn đề:
- card nhảy layout
- list/grid alignment dễ rung
- touch devices không được lợi gì

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

Vấn đề:
- không có loading
- không có empty state
- lỗi fetch không có chỗ xuất hiện

Good:

```tsx
if (isLoading) return <OrdersSkeleton />;
if (error) return <InlineError message="Không tải được đơn hàng" />;
if (orders.length === 0) return <EmptyState title="Chưa có đơn hàng" />;

return <OrderList orders={orders} />;
```

## Touch-Heavy Actions

Bad:

```tsx
<button className="h-8 px-2">Thanh toan</button>
```

Vấn đề:
- target quá nhỏ cho touch
- hierarchy yếu nếu action là primary

Good:

```tsx
<button className="min-h-[44px] px-4 text-sm font-medium">
  Thanh toan
</button>
```

## Visual Direction Drift

Bad:

```text
Task nhỏ trong app hiện có, nhưng tự đổi toàn bộ typography và màu CTA.
```

Vấn đề:
- phá design system
- tăng blast radius không cần thiết

Good:

```text
Giữ token và typography hiện có; chỉ mở visual direction mới nếu brief nói rõ vì sao.
```

## Dense Dashboard Layout

Bad:

```text
Nhét 14 metric cards, 3 charts, 2 filters và 4 CTA vào cùng một viewport đầu tiên.
```

Vấn đề:
- Hick's Law và Miller's Law bị phá
- không còn primary focus

Good:

```text
Nhóm metrics thành 5-7 item chính, secondary insights xuống dưới fold hoặc vào tab/filter.
```
