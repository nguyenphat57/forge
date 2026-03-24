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

> Muc tieu: giu `/bump` ro rang cho user Antigravity, nhung semver math va release checklist van di qua core.

## Process

1. Chot muc bump.
2. Preview hoac apply bang:

```powershell
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Tom tat `old -> new`, files doi, va verify tiep.

## Activation Announcement

```text
Forge Antigravity: bump | explicit release prep, still evidence-first
```
