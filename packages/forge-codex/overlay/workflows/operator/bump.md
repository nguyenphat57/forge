---
name: bump
type: flexible
triggers:
  - explicit request to bump version or prepare a release
  - optional alias: /bump
quality_gates:
  - Version bump only runs on an explicit bump/release request
  - Release verification steps are surfaced
  - Wrapper does not hide core semver/change checklist
---

# Bump - Codex Operator Wrapper

> Mục tiêu: giữ bump flow ngắn và rõ cho Codex, nhưng vẫn theo contract user-requested + justified semver của core.

## Process

1. Nếu user chưa nêu mức bump, suy luận từ repo diff và nêu lý do ngắn gọn.
2. Preview/apply bằng core planner:

```powershell
python scripts/prepare_bump.py --workspace <workspace>
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump minor --apply --release-ready
```

3. Trả lời ngắn:
   - version từ -> đến
   - bump source: explicit hay inferred
   - file đã đổi
   - verify nào phải chạy

## Activation Announcement

```text
Forge Codex: bump | release change with explicit or inferred semver
```
