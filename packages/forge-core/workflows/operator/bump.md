---
name: bump
type: flexible
triggers:
  - shortcut: /bump
  - user explicitly asks for a version bump or release prep
quality_gates:
  - User-requested only: do not treat generic wrap-up as a bump request
  - Current version is stated and target version is either explicit or justified by inference
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
   Nếu user chưa nêu `major|minor|patch`, suy luận từ git diff kể từ lần đổi `VERSION` gần nhất và nêu rõ lý do.
2. Preview hoặc apply bằng:

```powershell
python scripts/prepare_bump.py --workspace <workspace>
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Trả về:
   - current version
   - target version
   - bump source: explicit hay inferred
   - inference reasons / confidence nếu dùng auto
   - files sẽ đổi
   - verification commands cần chạy

## Output Contract

```text
Version: [... -> ...]
Bump source: [explicit|inferred]
Files đổi: [...]
Verify tiếp: [...]
```

## Activation Announcement

```text
Forge: bump | release prep with explicit or inferred semver
```
