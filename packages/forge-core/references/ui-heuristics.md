# UI Heuristics

> Heuristics global cho frontend/visualize, không gắn repo cụ thể.

## Touch-Heavy UI

- Primary actions nên nằm ở vùng dễ với tới, không sát mép gesture nếu là mobile/tablet.
- Các thao tác lặp lại hoặc tần suất cao nên có affordance rõ và target lớn.
- Đừng thiết kế flow phụ thuộc hover nếu sản phẩm chạm là chính.

## Dense Data UI

- Nhóm thông tin thành semantic blocks vừa mắt, thường 5-9 item chính mỗi cluster.
- Primary KPI phải nổi bật trước; secondary metrics có thể vào tabs, filters, hoặc secondary rows.
- Tránh noise như box-shadow nặng, border quá đậm, hoặc card nào cũng “đòi chú ý”.

## Dashboard UI

- Mỗi viewport đầu tiên nên có một hierarchy rõ: primary goal, primary KPI, primary action.
- Empty/loading/error của dashboard phải được thiết kế như screen thật, không chỉ là khoảng trống.
- Filters và time range controls cần rõ ảnh hưởng lên data nào.

## Perceived Performance

- UI phải phản hồi nhanh bằng skeleton, optimistic hint, disabled/loading state, hoặc inline feedback.
- Animation không được che việc app đang chậm hay đang fail.

## Decision Architecture

- Tránh “wall of buttons”.
- 1 hoặc tối đa 2 CTA chính mỗi view là mặc định an toàn; phần còn lại hạ cấp hoặc progressive disclosure.

## Accessibility Defaults

- Đừng chờ tới cuối mới nghĩ accessibility; focus order, contrast, labels, và motion boundaries phải xuất hiện ngay từ brief/spec.
