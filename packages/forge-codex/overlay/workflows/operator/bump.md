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

> Muc tieu: giu bump flow ngan va ro cho Codex, nhung van theo contract explicit-only cua core.

## Process

1. Chot muc bump (`patch`, `minor`, `major`) hoac version cu the.
2. Preview/apply bang core planner:

```powershell
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump minor --apply --release-ready
```

3. Tra loi ngan:
   - version tu -> den
   - file da doi
   - verify nao phai chay

## Activation Announcement

```text
Forge Codex: bump | explicit release change, no hidden version bumps
```
