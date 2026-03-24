# Frontend Stack Profiles

> Dùng khi task frontend cần một lens cụ thể theo stack thay vì guideline chung chung.

## generic-web

- Phù hợp khi stack chưa rõ hoặc task là UI reasoning trước implementation.
- Ưu tiên semantics, tokens, interaction cues, responsive states.
- Không mặc định framework-specific patterns khi artifact chưa chứng minh.

## html-tailwind

- Ưu tiên utility clarity, extracted patterns, theme tokens, stable hover/focus states.
- Watchouts:
  - class soup
  - arbitrary values tràn lan
  - `transition-all`
  - surface quá trong ở light mode

## react-vite

- Ưu tiên component boundaries theo screen regions và state ownership.
- Định nghĩa rõ loading/empty/error path trong brief trước khi code.
- Watchouts:
  - layout phụ thuộc state tạm thời không cần thiết
  - polish animation che mất rerender or state complexity

## nextjs

- Tách server/client boundary trước khi mô tả interaction phức tạp.
- Tính luôn loading and streaming placeholders vào UX contract.
- Watchouts:
  - design lệ thuộc client-only state mà không có fallback
  - hydration edge cases kéo lệch visual plan

## mobile-webview

- Dùng cho Capacitor/webview/tablet POS style work.
- Ưu tiên touch targets, safe-area, keyboard behavior, viewport resize resilience.
- Watchouts:
  - hover-centric interactions
  - actions đặt sát vùng gesture
  - dense layout chỉ đẹp trên desktop

## Reading Rule

- Chỉ chọn profile gần nhất với stack/task.
- Nếu vẫn chưa rõ stack, dùng `generic-web`.
- Nếu visual exploration cho mobile/tablet shell, thường `mobile-webview` hữu ích hơn `generic-web`.
