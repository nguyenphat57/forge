# Forge Workspace Init

> Mục tiêu: giữ phần khởi tạo workspace ở `forge-core` theo kiểu host-neutral, để adapter chỉ cần thêm wrapper `/init` và onboarding mà không fork skeleton logic.

## Core Contract

- Script canonical nằm tại `scripts/initialize_workspace.py`
- Script này chỉ tạo skeleton Forge tối thiểu có thể tái sử dụng qua nhiều host
- Adapter có thể thêm first-run UX, nhưng không được đổi shape của `.brain/` hay docs skeleton mà core đã chốt

## Skeleton Tối Thiểu

- `.brain/`
- `.brain/session.json`
- `docs/plans/`
- `docs/specs/`

Tùy chọn:

- adapter-global `state/preferences.json` nếu wrapper muốn seed default preferences ngay lúc init

## Workspace Classification

- `greenfield`: workspace rỗng hoặc chưa có repo state đáng kể -> next workflow mặc định là `brainstorm`
- `existing`: workspace đã có repo state -> next workflow mặc định là `plan`

## Hard Rules

- Không overwrite file đã tồn tại
- Không nhúng host-specific onboarding prose vào core script
- Không tạo README, command alias, hay memory ritual riêng của một host trong script này

## Adapter Boundary

- `forge-antigravity`: có thể đưa `/init` + onboarding mỏng dựa trên script này
- `forge-codex`: có thể expose init tối thiểu qua natural language mà không cần ceremony dày
- Adapter tương lai như `forge-claude` phải có thể tái sử dụng script này mà không đổi schema hay file layout
