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

> Muc tieu: chot `old -> new`, cap nhat artifact release can thiet, va dua ra checklist verify ro rang.

<HARD-GATE>
- Khong bump version neu user chua noi ro can bump/release.
- Khong claim release-ready chi vi da doi `VERSION`.
- Khong commit/push tu dong neu user chua yeu cau.
</HARD-GATE>

## Process

1. Xac dinh workspace release va muc bump.
2. Preview hoac apply bang:

```powershell
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Tra ve:
   - current version
   - target version
   - files se doi
   - verification commands can chay

## Output Contract

```text
Version: [... -> ...]
Files doi: [...]
Verify tiep: [...]
```

## Activation Announcement

```text
Forge: bump | explicit release prep, not generic wrap-up
```
