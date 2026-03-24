---
name: bump
type: flexible
triggers:
  - shortcut: /bump
  - user explicitly asks for a version bump or release prep
quality_gates:
  - User-requested only: do not treat generic wrap-up as a bump request
  - Current version is stated and target version is either explicit or justified by inference
  - Wrapper stays thin on top of core bump prep
---

# Bump - Antigravity Operator Wrapper

> Mục tiêu: giữ `/bump` rõ ràng cho user Antigravity, nhưng semver math và release checklist vẫn đi qua core.

## Process

1. Nếu user chưa nêu mức bump, suy luận từ repo diff và nêu lý do ngắn gọn.
2. Preview hoặc apply bằng:

```powershell
python scripts/prepare_bump.py --workspace <workspace>
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Tóm tắt:
   - version `old -> new`
   - bump source: explicit hay inferred
   - files đổi
   - verify tiếp

## Activation Announcement

```text
Forge Antigravity: bump | release prep with explicit or inferred semver
```
