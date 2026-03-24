---
name: bump
type: flexible
triggers:
  - shortcut: /bump
  - user explicitly asks for a version bump or release prep
quality_gates:
  - Explicit-only: do not treat generic wrap-up as a bump request
  - Current version and target version are both stated
  - Wrapper stays thin on top of core bump prep
---

# Bump - Antigravity Operator Wrapper

> Mục tiêu: giữ `/bump` rõ ràng cho user Antigravity, nhưng semver math và release checklist vẫn đi qua core.

## Process

1. Chốt mức bump.
2. Preview hoặc apply bằng:

```powershell
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Tóm tắt `old -> new`, files đổi, và verify tiếp.

## Activation Announcement

```text
Forge Antigravity: bump | explicit release prep, still evidence-first
```
