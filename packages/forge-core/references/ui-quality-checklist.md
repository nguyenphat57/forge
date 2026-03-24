# UI Quality Checklist

> Checklist delivery dùng chung cho `frontend` và `visualize`.

## Visual Direction

- [ ] Giữ design system hiện có hoặc nêu rõ vì sao phải mở rộng
- [ ] Typography, color, spacing có chủ đích
- [ ] Không dùng emoji như UI icons
- [ ] Icon set nhất quán nếu có icon

## Interaction Quality

- [ ] Clickable surfaces có affordance rõ
- [ ] Hover/focus states không gây layout shift
- [ ] Cursor phù hợp với phần tử tương tác trên web
- [ ] Không phụ thuộc hover cho hành vi cốt lõi trên touch surfaces

## States

- [ ] Default state rõ
- [ ] Loading state rõ
- [ ] Empty state rõ
- [ ] Error state rõ
- [ ] Destructive or confirmation state rõ khi cần

## Layout & Responsive

- [ ] Breakpoints chính đã được xem
- [ ] Không có horizontal scroll vô tình trên mobile
- [ ] Nội dung không bị che bởi sticky/fixed elements
- [ ] Touch targets >= 44px cho surfaces chạm

## Contrast & Theming

- [ ] Text contrast đủ đọc ở light mode
- [ ] Surface và border vẫn nhìn thấy được ở light mode
- [ ] Dark/light differences không làm mất hierarchy

## Motion

- [ ] Motion chủ yếu dùng `transform` và `opacity`
- [ ] Không dùng `transition: all`
- [ ] Có nghĩ đến `prefers-reduced-motion`

## Accessibility

- [ ] Focus order hợp lý
- [ ] Focus state rõ
- [ ] Form controls có label hoặc accessible name
- [ ] Không dùng màu làm tín hiệu duy nhất

## Anti-Patterns To Reject Fast

- Scale hover làm card nhảy layout
- Border quá mờ ở light mode
- Body text màu xám quá nhạt
- Chỉ làm happy path mà quên states hệ thống
- Thiết kế desktop-first cho màn hình touch-heavy
