# Forge Workspace Init

> Muc tieu: giu phan khoi tao workspace o `forge-core` theo kieu host-neutral, de adapter chi can them wrapper `/init` va onboarding ma khong fork skeleton logic.

## Core Contract

- Script canonical nam tai `scripts/initialize_workspace.py`
- Script nay chi tao skeleton Forge-toi-thieu co the tai su dung qua nhieu host
- Adapter co the them first-run UX, nhung khong duoc doi shape cua `.brain/` hay docs skeleton ma core da chot

## Skeleton Toi Thieu

- `.brain/`
- `.brain/session.json`
- `docs/plans/`
- `docs/specs/`

Tuy chon:

- `.brain/preferences.json` neu wrapper muon seed default preferences ngay luc init

## Workspace Classification

- `greenfield`: workspace rong hoac chua co repo state dang ke -> next workflow mac dinh la `brainstorm`
- `existing`: workspace da co repo state -> next workflow mac dinh la `plan`

## Hard Rules

- Khong overwrite file da ton tai
- Khong nhung host-specific onboarding prose vao core script
- Khong tao README, command alias, hay memory ritual rieng cua mot host trong script nay

## Adapter Boundary

- `forge-antigravity`: co the dua `/init` + onboarding mong dua tren script nay
- `forge-codex`: co the expose init toi thieu qua natural language ma khong can ceremony day
- Adapter tuong lai nhu `forge-claude` phai co the tai su dung script nay ma khong doi schema hay file layout
