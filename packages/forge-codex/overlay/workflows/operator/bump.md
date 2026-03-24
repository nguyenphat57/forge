---
name: bump
type: flexible
triggers:
  - explicit request to bump version or prepare a release
  - optional alias: /bump
quality_gates:
  - Version bump stays explicit-only
  - Release verification steps are surfaced
  - Wrapper does not hide core semver/change checklist
---

# Bump - Codex Operator Wrapper

> Mục tiêu: giữ bump flow ngắn và rõ cho Codex, nhưng vẫn theo contract explicit-only của core.

## Process

1. Chốt mức bump (`patch`, `minor`, `major`) hoặc version cụ thể.
2. Preview/apply bằng core planner:

```powershell
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump minor --apply --release-ready
```

3. Trả lời ngắn:
   - version từ -> đến
   - file đã đổi
   - verify nào phải chạy

## Activation Announcement

```text
Forge Codex: bump | explicit release change, no hidden version bumps
```
