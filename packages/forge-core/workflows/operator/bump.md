---
name: bump
type: flexible
triggers:
  - shortcut: /bump
  - user explicitly asks for a version bump or release prep
quality_gates:
  - Explicit-only: do not treat generic wrap-up as a bump request
  - Current version and target version are both stated
  - Verification commands are surfaced before any release claim
---

# Bump - Version Preparation

> Mục tiêu: chốt `old -> new`, cập nhật artifact release cần thiết, và đưa ra checklist verify rõ ràng.

<HARD-GATE>
- Không bump version nếu user chưa nói rõ cần bump/release.
- Không claim release-ready chỉ vì đã đổi `VERSION`.
- Không commit/push tự động nếu user chưa yêu cầu.
</HARD-GATE>

## Process

1. Xác định workspace release và mức bump.
2. Preview hoặc apply bằng:

```powershell
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Trả về:
   - current version
   - target version
   - files sẽ đổi
   - verification commands cần chạy

## Output Contract

```text
Version: [... -> ...]
Files đổi: [...]
Verify tiếp: [...]
```

## Activation Announcement

```text
Forge: bump | explicit release prep, not generic wrap-up
```
